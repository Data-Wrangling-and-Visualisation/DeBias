package main

import "errors"

var (
	ErrConfigNoSuchFile  = errors.New("[err01] provided config file does not exist")
	ErrConfigParseFailed = errors.New("[err02] failed to parse config file")
	ErrConfigInvalid     = errors.New("[err03] invalid config file option")
)
