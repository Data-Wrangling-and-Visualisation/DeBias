package main

import (
	"os"
	"time"

	"github.com/go-playground/validator/v10"
	"github.com/knadh/koanf/parsers/yaml"
	"github.com/knadh/koanf/providers/file"
	"github.com/knadh/koanf/v2"
)

type Config struct {
	// Debug is a flag to indicate whether to enable debug mode
	Debug bool `koanf:"debug" validate:""`
	// Metrics is a flag to indicate whether to enable metrics
	Metrics bool `koanf:"metrics" validate:""`
	// Spider is the spider configuration
	Spider SpiderConfig `koanf:"spider" validate:"required"`
	// Targets is a list of targets to be crawled
	Targets []TargetConfig `koanf:"targets" validate:"required"`
	// Redis is the redis configuration
	Redis RedisConfig `koanf:"redis" validate:"required"`
	// S3 is the s3 configuration
	S3 S3Config `koanf:"s3" validate:"required"`
	// MongoDB is the Mongodb configuration
	MongoDB MongoDBConfig `koanf:"mongodb" validate:"required"`
}

type SpiderConfig struct {
	// Workers is the number of workers to be spawned to crawl websites from the queue
	Workers int `koanf:"workers" validate:"required"`
	// CacheDir is the directory to store the downloaded files
	CacheDir string `koanf:"cache_dir" validate:"required"`
	// UserAgent is the user agent to be used by the spider
	UserAgent string `koanf:"user_agent" validate:"required"`
	// LimitRules is a list of LimitRule to be used to limit the number of concurrent requests to the websites
	LimitRules []struct {
		// DomainGlob is a glob pattern to match the domain, e.g. "*httpbin.*"
		DomainGlob string `koanf:"domain" validate:"required"`
		// Limit is a total number of goroutines (threads) to be spawned to crawl the website
		Limit int `koanf:"limit" validate:"required"`
		// Delay is the delay between each request to the website
		Delay time.Duration `koanf:"delay"`
	} `koanf:"limit_rules" validate:"required"`
}

type TargetConfig struct {
	// Name of the target, e.g. "example.com" or "news-website"
	Name string `koanf:"name" validate:"required"`
	// Root is the root url of the target website, spider will recursively crawl the website
	Root string `koanf:"root" validate:"required,http_url"`
	// Render is a flag to indicate whether to utilize javascript rendering
	Render bool `koanf:"render" validate:""`
	// DomainOnly is a flag to indicate whether to crawl only the domain of the target.
	// E.g. if example.com references another.com, spider will crawl example.com but not another.com if DomainOnly is true
	DomainOnly bool `koanf:"domain_only" validate:""`
	// RateLimit is the number of requests per second to be made to the target website
	RateLimit int `koanf:"rate_limit" validate:""`
	// RefFilters is a list of selectors to be used to find references on the website. E.g. ".next a[href]"
	RefFilters []string `koanf:"ref_filters" validate:""`
}

type RedisConfig struct {
	// Address is the redis address, e.g. "localhost:6379"
	Address string `koanf:"address" validate:"required"`
	// Password is the password to authenticate to the redis server, optional
	Password string `koanf:"password"`
	// DB is the redis database to use, optional
	DB int `koanf:"db"`
	// Prefix is the prefix to be used for all keys in redis, optional
	Prefix string `koanf:"prefix"`
}

type S3Config struct {
	// Endpoint is the s3 endpoint, e.g. "s3.amazonaws.com"
	Endpoint string `koanf:"endpoint" validate:"required"`
	// Region is the s3 region, e.g. "us-east-1"
	Region string `koanf:"region" validate:"required"`
	// AccessKey is the s3 access key
	AccessKey string `koanf:"access_key" validate:"required"`
	// SecretKey is the s3 secret key
	SecretKey string `koanf:"secret_key" validate:"required"`
	// Bucket is the s3 bucket name
	Bucket string `koanf:"bucket" validate:"required"`
	// SSL sets whether to use HTTPS or HTTP
	SSL bool `koanf:"ssl" validate:""`
}

type MongoDBConfig struct {
	// URL is a string defining connection to mongodb clustrer
	URL string `koanf:"url" validate:"required"`
	// Db is a database to use
	Db string `koanf:"db" validate:"required"`
	// Collection is a collection to use
	Collection string `koanf:"collection" validate:"required"`
}

// LoadConfig loads the config file from the given path
func LoadConfig(filepath string) (Config, error) {
	if _, err := os.Stat(filepath); err != nil {
		return Config{}, err
	}

	k := koanf.New(".")
	if err := k.Load(file.Provider(filepath), yaml.Parser()); err != nil {
		return Config{}, err
	}

	config := Config{}
	if err := k.Unmarshal("", &config); err != nil {
		return Config{}, err
	}

	validate := validator.New(validator.WithRequiredStructEnabled())
	if err := validate.Struct(config); err != nil {
		return Config{}, err
	}

	return config, nil
}

// MustLoadConfig is a helper function to load the config file and panic if an error occurs
func MustLoadConfig(filepath string) Config {
	config, err := LoadConfig(filepath)
	if err != nil {
		panic(err)
	}
	return config
}
