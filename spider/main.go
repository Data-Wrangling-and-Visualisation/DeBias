package main

import (
	"context"
	"flag"
	"log"
	"os"
	"os/signal"
	"syscall"
)

var (
	configPath string
	ctx        context.Context
	cancel     context.CancelFunc
)

func init() {
	flag.StringVar(&configPath, "config", "config.yaml", "Path to the configuration file")
	ctx, cancel = context.WithCancel(context.Background())
}

func main() {
	flag.Parse()

	// Load configuration
	config, err := LoadConfig(configPath)
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	for _, target := range config.Targets {
		if target.Render {
			log.Printf("Detected browser usage required. Downloading browser instance before starting spider...")
			InitBrowser()
			break
		}
	}

	// Create and start the spider
	spider, err := NewSpider(config)
	if err != nil {
		log.Fatalf("Failed to create spider: %v", err)
	}

	if err := spider.Start(); err != nil {
		log.Fatalf("Failed to start spider: %v", err)
	}

	// Wait for interrupt signal to gracefully stop the spider
	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt, syscall.SIGTERM)
	<-c

	log.Println("Stopping spider...")
	cancel()
	spider.Stop()

	if browser != nil {
		log.Println("Closing browser...")
		browser.MustClose()
	}
}
