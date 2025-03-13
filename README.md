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
    - [Experiments](#experiments)
    - [Data Scraping](#data-scraping)
  - [Deploy](#deploy)
    - [Port Mapping](#port-mapping)
    - [Using external S3 provider](#using-external-s3-provider)
    - [Using local S3 provider](#using-local-s3-provider)
    - [Remove services](#remove-services)
  - [Current state](#current-state)
    - [Distribution of political positions overall](#distribution-of-political-positions-overall)
    - [Distribution of political positions in the USA](#distribution-of-political-positions-in-the-usa)
    - [Distribution of political positions in the UK](#distribution-of-political-positions-in-the-uk)
    - [Bonus: Distribution of political positions of sources which require VPN](#bonus-distribution-of-political-positions-of-sources-which-require-vpn)


## Overview

The repository is dedicated to the Debias project, dedicated to showing relationships between different concepts in the news. 

We cover different geographical locations (mainly USA and UK), different political positions (taken from [AllSides](https://www.allsides.com/unbiased-balanced-news)) and varios news providers.

The final goal is to create an interactive visualization, which would show how concepts are interconnected within different time stamps and from different points of view.

## Technologies

### Experiments
- <img src=".github/assets/Python-logo-notext.svg.png" width="16" height="16"></img> Python

### Data Scraping
- <img src=".github/assets/4373190_docker_logo_logos_icon.png" width="16" height="16"></img> Docker 
- <img src=".github/assets/Go-Logo_Blue.png" width="16" height="16"></img> Go 
- <img src=".github/assets/colly.png" width="16" height="16"></img> Colly 
- <img src=".github/assets/redis.svg" width="16" height="16"></img> Redis 
- <img src=".github/assets/minio-1.svg" width="16" height="16"></img> Minio 
- <img src=".github/assets/mongodb-icon-1.svg" width="16" height="16"></img> MongoDB 

## Deploy

The initial version is available at https://data-wrangling-and-visualisation.github.io/DeBias/

### Port Mapping

| Service       | Port  |
| ------------- | ----- |
| Spider        | 11001 |
| Cache         | 11002 |
| MongoDB       | 11003 |
| MinIO         | 11004 |
| MinIO Console | 11005 |

### Using external S3 provider

0. Create `.env` file
Fill in the following variables:
```bash
MONGO_USERNAME=...
MONGO_PASSWORD=...
```

1. Create `spider/config.yaml`

> [!NOTE]
> You can find example configuration in [`spider/example.config.yaml`](spider/example.config.yaml)

2. Run services

```bash
docker compose -f s3.docker-compose.yml up --build --detach
```

### Using local S3 provider

0. Create `.env` file
Fill in the following variables:
```bash
MONGO_USERNAME=...
MONGO_PASSWORD=...
MINIO_ACCESS_KEY=...
MINIO_SECRET_KEY=...
MINIO_BUCKET=...
```


1. Create MinIO S3 service using docker:
```bash
docker compose -f minio.docker-compose.yml up minio_setup
```

2. Create `spider/config.yaml`

> [!NOTE]
> You can find example configuration in [`spider/example.config.yaml`](spider/example.config.yaml)

3. Run services

```bash
docker compose -f minio.docker-compose.yml up --build --detach
```

### Remove services

To stop all remove all containers AND THEIR VOLUMES:
```bash
docker compose -f minio.docker-compose.yml down --volumes
# or
docker compose -f s3.docker-compose.yml down --volumes
```


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