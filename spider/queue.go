package main

import (
	"fmt"

	"github.com/go-redis/redis/v8"
)

type RedisQueue struct {
	client *redis.Client
	prefix string
}

func NewRedisQueue(cfg RedisConfig) *RedisQueue {
	client := redis.NewClient(&redis.Options{
		Addr:     cfg.Address,
		Password: cfg.Password,
		DB:       cfg.DB,
	})

	return &RedisQueue{
		client: client,
		prefix: cfg.Prefix,
	}
}

func (rq *RedisQueue) AddURL(queueName string, URL string) error {
	key := fmt.Sprintf("%squeue:%s", rq.prefix, queueName)
	return rq.client.RPush(ctx, key, URL).Err()
}

func (rq *RedisQueue) GetURL(queueName string) (string, error) {
	key := fmt.Sprintf("%squeue:%s", rq.prefix, queueName)
	return rq.client.LPop(ctx, key).Result()
}

func (rq *RedisQueue) QueueSize(queueName string) (int64, error) {
	key := fmt.Sprintf("%squeue:%s", rq.prefix, queueName)
	return rq.client.LLen(ctx, key).Result()
}
