# De Bias

<div align = center><img src=".github/assets/banner.png"><br><br>

&ensp;[<kbd> <br> Overview <br> </kbd>](#overview)&ensp;
&ensp;[<kbd> <br> Technologies <br> </kbd>](#technologies)&ensp;
&ensp;[<kbd> <br> Deploy <br> </kbd>](#deploy)&ensp;
&ensp;[<kbd> <br> Current state <br> </kbd>](#current-state)&ensp;
<br><br><br><br></div>

## Table of Contents
- [De Bias](#de-bias)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Technologies](#technologies)
  - [Services](#services)
    - [Scraper](#scraper)
    - [Renderer](#renderer)
    - [Processor](#processor)
    - [Server](#server)
    - [Metastore](#metastore)
    - [S3](#s3)
    - [Wordstore](#wordstore)
    - [Message queue](#message-queue)
  - [Deploy](#deploy)
    - [Using external S3 provider](#using-external-s3-provider)
    - [Using local S3 provider](#using-local-s3-provider)
    - [Remove services](#remove-services)
  - [Development](#development)
    - [Structure](#structure)
    - [Adding new service](#adding-new-service)
  - [Current state](#current-state)
    - [Distribution of political positions overall](#distribution-of-political-positions-overall)
    - [Distribution of political positions in the USA](#distribution-of-political-positions-in-the-usa)
    - [Distribution of political positions in the UK](#distribution-of-political-positions-in-the-uk)
    - [Bonus: Distribution of political positions of sources which require VPN](#bonus-distribution-of-political-positions-of-sources-which-require-vpn)


## Overview

The repository is dedicated to the Debias project, dedicated to showing relationships between different concepts in the news. 

We cover different geographical locations (mainly USA and UK), different political positions (taken from [AllSides](https://www.allsides.com/unbiased-balanced-news)) and various news providers.

The final goal is to create an interactive visualization, which would show how concepts are interconnected within different time stamps and from different points of view.

## Technologies

- <img src=".github/assets/python.png" width="16" height="16"></img> Python
- <img src=".github/assets/docker.png" width="16" height="16"></img> Docker
- <img src=".github/assets/redis.svg" width="16" height="16"></img> Redis 
- <img src=".github/assets/minio.svg" width="16" height="16"></img> MinIO
- <img src=".github/assets/nats.png" width="16" height="16"></img> NATS
- <img src=".github/assets/postgres.svg" width="16" height="16"></img> Postgres 

## Services

![Architecture](.github/assets/architecture.png)

### [Scraper](debias/scraper/readme.md)
Scaper is a service which scrapers news from different news providers. This service is recursively calling itself to scrape the next news pages.
If page requires rendering, it will be sent to the `renderer` service. If page is static, it is stored in the `s3` service, metadata is stored in the `metastore` service, and a `processor` service is called to process the page.

### [Renderer](debias/renderer/readme.md)
Renderer is a service which renders news pages using browser API. It is called by the `scraper` service. After render, it saves HTML content to the `s3` service and metadata to the `metastore` service and sends a request to the `processor` service to process the page.

### [Processor](debias/processor/readme.md)
Processor is a service which processes news pages. It extracts human-readable text from the page, performs NLP pipelines and stores the results in the `wordstore` service.

### [Server](debias/server/readme.md)
Web server which serves the results of the `processor`. It aggregates the statistics of the words, precomputes and caches aggregations, and serves them to the client. It serves the frontend files as well.

### Metastore
A postgres database which stores metadata of the scraped pages.

### S3
A S3 provider which stores the static pages. Could be a local MinIO deployment or an external S3 cloud service.

### Wordstore
A postgres database which stores the words of the processed pages.

### Message queue
A NATS message queue which is used for S2S communication.


## Deploy

The initial version is available at https://data-wrangling-and-visualisation.github.io/DeBias/

### Using external S3 provider

0. Create `.env` file
Fill in the following variables:
```bash
PG_USERNAME=...
PG_PASSWORD=...
```

1. Create `debias/scraper/config.toml`

> [!NOTE]
> You can find example configuration in [`debias/scraper/example.config.toml`](debias/scraper/example.config.toml)

2. Run services

```bash
docker compose -f docker-compose.yml up --build --detach
```

### Using local S3 provider

0. Create `.env` file
Fill in the following variables:
```bash
MINIO_ACCESS_KEY=...
MINIO_SECRET_KEY=...
MINIO_BUCKET=...
```

1. Create MinIO S3 service using docker:
```bash
docker compose -f minio.docker-compose.yml up minio_setup
```

2. Create `debias/scraper/config.toml`

> [!NOTE]
> You can find example configuration in [`debias/scraper/example.config.toml`](debias/scraper/example.config.toml)

3. Run services

```bash
docker compose -f minio.docker-compose.yml up --build --detach
```

### Remove services

To stop all remove all containers AND THEIR VOLUMES:
```bash
docker compose -f minio.docker-compose.yml down --volumes
# or
docker compose -f docker-compose.yml down --volumes
```

## Development

### Structure
```
.
├── debias       # shared code root
│   ├── core     # reusable components - s3, metastore, configs, etc
│   └── scraper   # scraper related code
```

### Adding new service
To add new service:
1. Create new directory in `debias` directory
2. Create `dockerfile` prefixed with `servicename` (e.g. `scraper.dockerfile`)
3. Add all the required dependencies to `pyproject.toml` under `--group servicename`



## Current state

We have collected 38 sources of news from USA and UK and found out their political positions.

### Distribution of political positions overall
<img src=".github/assets/Political bias distribution-2.png"></img>

### Distribution of political positions in the USA
<img src=".github/assets/Political bias distribution - USA-2.png"></img>

### Distribution of political positions in the UK
<img src=".github/assets/Political bias distribution - UK-2.png"></img>

### Bonus: Distribution of political positions of sources which require VPN
<img src=".github/assets/Political bias distribution for sites that require VPN-2.png"></img>

It seems left parties are indeed more liberal.

We have parsed several news articles using python and prepared a deployment describing general trends in these articles.

The deployment can be found on [Github Pages](https://data-wrangling-and-visualisation.github.io/DeBias/)