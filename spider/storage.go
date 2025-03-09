package main

import (
	"fmt"
	"log/slog"
	"net/url"

	"github.com/go-redis/redis/v8"
)

type RedisStorage struct {
	client *redis.Client
	prefix string
}

func NewRedisStorage(cfg RedisConfig) *RedisStorage {
	client := redis.NewClient(&redis.Options{
		Addr:     cfg.Address,
		Password: cfg.Password,
		DB:       cfg.DB,
	})

	return &RedisStorage{
		client: client,
		prefix: cfg.Prefix,
	}
}

func (rs *RedisStorage) Init() error {
	return nil
}

func (rs *RedisStorage) Visited(requestID uint64) error {
	key := fmt.Sprintf("%sreq:%d", rs.prefix, requestID)
	return rs.client.Set(ctx, key, "1", 0).Err()
}

func (rs *RedisStorage) IsVisited(requestID uint64) (bool, error) {
	key := fmt.Sprintf("%sreq:%d", rs.prefix, requestID)
	val, err := rs.client.Get(ctx, key).Result()
	if err == redis.Nil {
		return false, nil
	}
	return val == "1", err
}

func (rs *RedisStorage) Cookies(u *url.URL) string {
	key := fmt.Sprintf("%scookie:%s", rs.prefix, u.String())
	val, err := rs.client.Get(ctx, key).Result()
	if err == redis.Nil {
		return ""
	}
	return val
}

func (rs *RedisStorage) SetCookies(u *url.URL, cookies string) {
	key := fmt.Sprintf("%scookie:%s", rs.prefix, u.String())
	if err := rs.client.Set(ctx, key, cookies, 0).Err(); err != nil {
		slog.Warn("failed to set cookies", "url", u)
	}
}
