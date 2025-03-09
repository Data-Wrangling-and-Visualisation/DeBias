package main

import (
	"crypto/md5"
	"encoding/hex"
	"fmt"
	"log"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/credentials"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/s3"
	"github.com/go-redis/redis/v8"
	"github.com/gocolly/colly/v2"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

// Metadata represents the document to be stored in MongoDB
type Metadata struct {
	URL        string    `bson:"url"`
	Domain     string    `bson:"domain"`
	Datetime   time.Time `bson:"datetime"`
	TargetName string    `bson:"target_name"`
	Hash       string    `bson:"hash"`
}

// Spider handles the web crawling
type Spider struct {
	config      Config
	mongoClient *mongo.Client
	s3Client    *s3.S3
	redisQueue  *RedisQueue
	wg          sync.WaitGroup
}

func NewSpider(config Config) (*Spider, error) {
	// Initialize MongoDB connection
	mongoOptions := options.Client().ApplyURI(config.MongoDB.URL)
	mongoClient, err := mongo.Connect(ctx, mongoOptions)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to MongoDB: %w", err)
	}

	// Initialize S3 client
	s3Config := &aws.Config{
		Endpoint:         aws.String(config.S3.Endpoint),
		Region:           aws.String(config.S3.Region),
		Credentials:      credentials.NewStaticCredentials(config.S3.AccessKey, config.S3.SecretKey, ""),
		S3ForcePathStyle: aws.Bool(true),
		DisableSSL:       aws.Bool(!config.S3.SSL),
	}
	s3Session, err := session.NewSession(s3Config)
	if err != nil {
		return nil, fmt.Errorf("failed to create S3 session: %w", err)
	}
	s3Client := s3.New(s3Session)

	// Initialize Redis queue
	redisQueue := NewRedisQueue(config.Redis)

	return &Spider{
		config:      config,
		mongoClient: mongoClient,
		s3Client:    s3Client,
		redisQueue:  redisQueue,
	}, nil
}

func (s *Spider) Start() error {
	// Create cache directory if it doesn't exist
	if err := os.MkdirAll(s.config.Spider.CacheDir, 0755); err != nil {
		return fmt.Errorf("failed to create cache directory: %w", err)
	}

	// Start workers
	for i := 0; i < s.config.Spider.Workers; i++ {
		s.wg.Add(1)
		go s.worker(i)
	}

	log.Printf("Started %d workers", s.config.Spider.Workers)

	// Add targets to the queue if queue is empty
	for _, target := range s.config.Targets {
		qSize, err := s.redisQueue.QueueSize(target.Name)
		if err != nil {
			log.Printf("Failed to get queue size for target %s: %v", target.Name, err)
			continue
		}

		if qSize == 0 {
			if err := s.redisQueue.AddURL(target.Name, target.Root); err != nil {
				log.Printf("Failed to add root URL for target %s: %v", target.Name, err)
			} else {
				log.Printf("Added root URL %s for target %s", target.Root, target.Name)
			}
		}
	}

	return nil
}

func (s *Spider) Stop() {
	s.wg.Wait()
	if err := s.mongoClient.Disconnect(ctx); err != nil {
		log.Printf("Failed to disconnect from MongoDB: %v", err)
	}
}

func (s *Spider) worker(id int) {
	defer s.wg.Done()
	log.Printf("Worker %d started", id)

	for {
		select {
		case <-ctx.Done():
			log.Printf("Worker %d stopping due to context cancellation", id)
			return
		default:
			// Try to fetch work from each target queue
			for _, target := range s.config.Targets {
				url, err := s.redisQueue.GetURL(target.Name)
				if err == redis.Nil || err != nil {
					continue // Queue is empty or error occurred
				}

				log.Printf("Worker %d processing URL %s for target %s", id, url, target.Name)
				s.processURL(url, &target)
				break // Process one URL at a time
			}

			// Small sleep to prevent tight loop if all queues are empty
			time.Sleep(100 * time.Millisecond)
		}
	}
}

func (s *Spider) processURL(URL string, target *TargetConfig) {
	// Initialize collector
	c := colly.NewCollector(
		colly.AllowedDomains(getDomainFromURL(URL)),
		colly.CacheDir(s.config.Spider.CacheDir),
	)

	// Apply rate limiting rules
	for _, rule := range s.config.Spider.LimitRules {
		err := c.Limit(&colly.LimitRule{
			DomainGlob:  rule.DomainGlob,
			Parallelism: rule.Limit,
			Delay:       rule.Delay,
		})
		if err != nil {
			log.Printf("Failed to set limit rule: %v", err)
		}
	}

	// Use Redis for storing visited URLs
	redisStorage := NewRedisStorage(s.config.Redis)
	c.SetStorage(redisStorage)

	// Handle response
	c.OnResponse(func(r *colly.Response) {
		url := r.Request.URL.String()
		domain := getDomainFromURL(url)
		now := time.Now()

		// Generate content hash
		hash := md5.Sum(r.Body)
		hashStr := hex.EncodeToString(hash[:])

		var htmlContent []byte
		if target.Render {
			// Use Rod to render JavaScript
			renderedHTML, err := renderJavaScript(url)
			if err != nil {
				log.Printf("Failed to render JavaScript for URL %s: %v", url, err)
				htmlContent = r.Body
			} else {
				htmlContent = []byte(renderedHTML)
			}
		} else {
			htmlContent = r.Body
		}

		// Save to S3
		objectKey := fmt.Sprintf("%s/%s/%s.html", target.Name, domain, hashStr)
		_, err := s.s3Client.PutObject(&s3.PutObjectInput{
			Bucket: aws.String(s.config.S3.Bucket),
			Key:    aws.String(objectKey),
			Body:   strings.NewReader(string(htmlContent)),
		})
		if err != nil {
			log.Printf("Failed to save to S3: %v", err)
		}

		// Save metadata to MongoDB
		metadata := Metadata{
			URL:        url,
			Domain:     domain,
			Datetime:   now,
			TargetName: target.Name,
			Hash:       hashStr,
		}

		collection := s.mongoClient.Database(s.config.MongoDB.Db).Collection(s.config.MongoDB.Collection)
		_, err = collection.InsertOne(ctx, metadata)
		if err != nil {
			log.Printf("Failed to save metadata to MongoDB: %v", err)
		}

		log.Printf("Processed URL: %s, saved with hash: %s", url, hashStr)
	})

	// Handle links
	c.OnHTML("a[href]", func(e *colly.HTMLElement) {
		link := e.Attr("href")
		absoluteURL := e.Request.AbsoluteURL(link)
		if absoluteURL == "" {
			return
		}

		// Skip if we should only process the same domain and the link is external
		if target.DomainOnly && getDomainFromURL(absoluteURL) != getDomainFromURL(URL) {
			return
		}

		// Add the URL to the queue
		err := s.redisQueue.AddURL(target.Name, absoluteURL)
		if err != nil {
			log.Printf("Failed to add URL %s to queue: %v", absoluteURL, err)
		}
	})

	// Apply custom ref filters if provided
	if len(target.RefFilters) > 0 {
		for _, filter := range target.RefFilters {
			c.OnHTML(filter, func(e *colly.HTMLElement) {
				link := e.Attr("href")
				if link == "" {
					return
				}

				absoluteURL := e.Request.AbsoluteURL(link)
				if absoluteURL == "" {
					return
				}

				// Skip if we should only process the same domain and the link is external
				if target.DomainOnly && getDomainFromURL(absoluteURL) != getDomainFromURL(URL) {
					return
				}

				// Add the URL to the queue
				err := s.redisQueue.AddURL(target.Name, absoluteURL)
				if err != nil {
					log.Printf("Failed to add URL %s to queue: %v", absoluteURL, err)
				}
			})
		}
	}

	// Handle errors
	c.OnError(func(r *colly.Response, err error) {
		log.Printf("Error processing %s: %v", r.Request.URL, err)
	})

	// Start scraping
	err := c.Visit(URL)
	if err != nil {
		log.Printf("Failed to visit URL %s: %v", URL, err)
	}
}
