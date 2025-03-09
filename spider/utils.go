package main

import (
	"net/url"
	"strings"

	"github.com/go-rod/rod"
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

func renderJavaScript(urlStr string) (string, error) {
	// Launch a browser
	browser := rod.New().MustConnect()
	defer browser.Close()

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
