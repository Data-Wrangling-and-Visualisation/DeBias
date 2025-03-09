package main

import "github.com/gocolly/colly/v2"

func main() {
	cfg := MustLoadConfig("config.yaml")
	_ = cfg

	c := colly.NewCollector()
	_ = c
}
