# De Bias

<div align = center><img src=".github/assets/banner.png"><br><br>

&ensp;[<kbd> <br> Overview <br> </kbd>](#overview)&ensp;
&ensp;[<kbd> <br> Technologies <br> </kbd>](#technologies)&ensp;
&ensp;[<kbd> <br> Deploy <br> </kbd>](#deploy)&ensp;
&ensp;[<kbd> <br> EDA <br> </kbd>](#eda)&ensp;
&ensp;[<kbd> <br> Visualization <br> </kbd>](#visualization)&ensp;
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
    - [Scale services for better performance!](#scale-services-for-better-performance)
    - [Remove services](#remove-services)
  - [Development](#development)
    - [Structure](#structure)
    - [Adding new service](#adding-new-service)
    - [Frontend Development](#frontend-development)
  - [EDA](#eda)
    - [Distribution of political positions overall](#distribution-of-political-positions-overall)
    - [Distribution of political positions in the USA](#distribution-of-political-positions-in-the-usa)
    - [Distribution of political positions in the UK](#distribution-of-political-positions-in-the-uk)
    - [Bonus: Distribution of political positions of sources which require VPN](#bonus-distribution-of-political-positions-of-sources-which-require-vpn)
  - [Visualization](#visualization)


## Overview

The repository is dedicated to the Debias project, dedicated to showing relationships between different concepts in the news. 

We cover different geographical locations (mainly USA and UK), different political positions (taken from [AllSides](https://www.allsides.com/unbiased-balanced-news)) and various news providers.

The final goal is to create an interactive visualization, which would show how concepts are interconnected within different time stamps and from different points of view.

![overiew diagram](.github/assets/diagram.png)

## Technologies

- <img src=".github/assets/python.png" width="16" height="16"></img> Python
- <img src=".github/assets/docker.png" width="16" height="16"></img> Docker
- <img src=".github/assets/redis.svg" width="16" height="16"></img> Redis 
- <img src=".github/assets/minio.svg" width="16" height="16"></img> MinIO
- <img src=".github/assets/nats.png" width="16" height="16"></img> NATS
- <img src=".github/assets/postgres.svg" width="16" height="16"></img> Postgres 
- <img src=".github/assets/playwright.svg" width="16" height="16"></img> Playwright
- <img src=".github/assets/litestar.svg" width="16" height="16"></img> Litestar
- <img src=".github/assets/polars.webp" width="16" height="16"></img> Polars
- <img src=".github/assets/d3.png" width="16" height="16"></img> D3.js

### NLP:
- <img src=".github/assets/huggingface.svg" width="16" height="16"></img> Transfrormers
- <img src=".github/assets/spacy.svg" width="16" height="16"></img> SpaCy

## Services

![Architecture](.github/assets/architecture.png)

### [Scraper](debias/scraper/readme.md)
Scaper is a service which scrapers news from different news providers. This service is recursively calling itself to scrape the next news pages.
If page requires rendering, it will be sent to the `renderer` service. If page is static, it is stored in the `s3` service, metadata is stored in the `metastore` service, and a `processor` service is called to process the page.

### [Renderer](debias/renderer/readme.md)
Renderer is a service which renders news pages using browser API. It is called by the `scraper` service. After render, it saves HTML content to the `s3` service and metadata to the `metastore` service and sends a request to the `processor` service to process the page.

### [Processor](debias/processor/readme.md)
Processor is a service which processes news pages. It extracts human-readable text from the page, performs NLP pipelines and stores the results in the `wordstore` service.

#### NLP pipeline
- **Classifier**
  - A *zero-shot classifier* from HuggingFace Transformers. In particular, `MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli` due to it's comparably low size.
- **Extractor**
  - A keyword exctraction algorithm with SpaCy. SpaCy is used to extract Named Entities, which are used as keywords after processing.


### [Server](debias/server/readme.md)
Web server which serves the results of the `processor`. It aggregates the statistics of the words, precomputes and caches aggregations, and serves them to the client. It serves the frontend files as well.

### Metastore
A postgres database which stores metadata of the scraped pages.

### S3
A S3 provider which stores the static pages. Could be a local MinIO deployment or an external S3 cloud service.

### Wordstore
A postgres database which stores the processed pages, keywords, topics, and their corresponding frequencies.

### Message queue
A NATS message queue which is used for S2S communication.


## Deploy

The Javascript visualization is available at https://debias.dartt0n.ru/

### Using external S3 provider

0. Create `.env` file
Fill in the following variables:
```bash
PG_USERNAME=...
PG_PASSWORD=...
```

1. Create configuration files

- `debias/scraper/config.toml`
- `debias/server/config.toml`
- `debias/processor/config.toml`
- `debias/renderer/config.toml`

> [!NOTE]
> You can find example configuration in the following files:
> - [`debias/scraper/example.config.toml`](debias/scraper/example.config.toml)
> - [`debias/server/example.config.toml`](debias/server/example.config.toml)
> - [`debias/processor/example.config.toml`](debias/processor/example.config.toml)
> - [`debias/renderer/example.config.toml`](debias/renderer/example.config.toml)

2. Pre-download ML models
```bash
mkdir models
uv run --group processor download-models.py
```

3. Run services

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

PG_USERNAME=...
PG_PASSWORD=...
```

1. Create configuration files

- `debias/scraper/config.toml`
- `debias/server/config.toml`
- `debias/processor/config.toml`
- `debias/renderer/config.toml`

> [!NOTE]
> You can find example configuration in the following files:
> - [`debias/scraper/example.config.toml`](debias/scraper/example.config.toml)
> - [`debias/server/example.config.toml`](debias/server/example.config.toml)
> - [`debias/processor/example.config.toml`](debias/processor/example.config.toml)
> - [`debias/renderer/example.config.toml`](debias/renderer/example.config.toml)

2. Pre-download ML models
```bash
mkdir models
uv run --group processor download-models.py
```

3. Create MinIO S3 service using docker:
```bash
docker compose -f minio.docker-compose.yml up minio_setup
```

### Scale services for better performance!

The following services could be automatically scaled horizontally for better performance:
- scraper
- renderer
- processor

For easy scaling use docker-compose `--scale` option.

E.g., the following command will launch 5 `scaper instances, 2 `renderer` instances. 2 `processor` instances:
```bash
docker compose up --detach \
  --scale scaper=5 \
  --scale renderer=2 \
  --scale processor=2\
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
├── debias          # shared code root
│   ├── core        # reusable components - s3, metastore, configs, etc
│   └── scraper     # scraper related code
│   └── processor   # NLP processor related code
│   └── renderer    # browser renderer related code
│   └── server      # server related code
│       └── frontend   # frontend related code

```

### Adding new service
To add new service:
1. Create new directory in `debias` directory
2. Create `dockerfile` prefixed with `servicename` (e.g. `scraper.dockerfile`)
3. Add all the required dependencies to `pyproject.toml` under `--group servicename`
4. Add new package to `tool.hatch.build.targets.wheel` config in `pyproject.toml`

### Frontend Development

0. Create `.env` file
Fill in the following variables:
```bash
PG_USERNAME=...
PG_PASSWORD=...
```

1. Launch database container
Using docker-compose:
```bash
docker compose up -d database
```

2. Generate random data
Set environment variable `POSTGRES_CONNECTION` to the connection string of the database (replace `USERNAME` and `PASSWORD` with your actual username and password):
```bash
POSTGRES_CONNECTION="postgresql://USERNAME:$PASSWORD$@localhost:5432/postgres" uv run generate-data.py
```

3. Create server configuration file `config.toml`
Replace `USERNAME` and `PASSWORD` with your actual username and password: 
```toml
[pg]
connection = "postgresql://${PG_USERNAME}:${PG_PASSWORD}$@localhost:5432/postgres"
```

4. Launch backend server with hot reload
```bash
CONFIG=config.toml uv run litestar --app debias.server:app run --debug --reload
```


## EDA

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


## Visualization

The visualization is divided into 3 parts:

1. Comparison of topics distribution for Left-Leaning and Right-Leaning media.
2. Comparison of keywords networks for Left-Leaning and Right-Leaning media.
3. Sandbox network with filtering functionality.

All visualizations are created using D3.js.

You can view the visualization at https://debias.dartt0n.ru/

### Visualization example

<img src=".github/assets/visualization.png"></img>
