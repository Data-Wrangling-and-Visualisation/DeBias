package main

import (
	"log"
	"net/url"
	"strings"
	"sync"

	"github.com/go-rod/rod"
	"github.com/go-rod/rod/lib/launcher"
)

func getDomainFromURL(urlStr string) string {
	u, err := url.Parse(urlStr)
	if err != nil {
		return ""
	}
	return u.Hostname()
}

func normalizeURL(urlStr string) string {
	u, err := url.Parse(urlStr)
	if err != nil {
		return urlStr
	}

	// Remove fragment
	u.Fragment = ""

	// Remove default port
	if (u.Scheme == "http" && u.Port() == "80") || (u.Scheme == "https" && u.Port() == "443") {
		host := u.Hostname()
		u.Host = host
	}

	// Convert to lowercase
	u.Scheme = strings.ToLower(u.Scheme)
	u.Host = strings.ToLower(u.Host)

	return u.String()
}

var (
	browser *rod.Browser
	once    sync.Once
)

// InitBrowser initializes and downloads the browser once
func InitBrowser() {
	once.Do(func() {
		log.Println("Downloading and initializing headless browser...")
		// Just download the browser and prepare the launcher
		url := launcher.New().Bin("/usr/bin/chromium-browser").Headless(true).MustLaunch()
		browser = rod.New().ControlURL(url).MustConnect()
		log.Println("Browser initialized successfully")
	})
}

// GetBrowser returns the initialized browser or initializes it if needed
func GetBrowser() *rod.Browser {
	if browser == nil {
		InitBrowser()
	}
	return browser
}

func renderJavaScript(urlStr string) (string, error) {
	// Get the shared browser instance
	browser := GetBrowser()

	// Navigate to the URL
	page := browser.MustPage(urlStr)

	// Wait for the page to be loaded
	page.MustWaitStable()

	// Get the HTML content
	html, err := page.HTML()
	if err != nil {
		return "", err
	}

	return html, nil
}
