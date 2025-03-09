# De Bias

<div align = center><img src=".github/assets/banner.png"><br><br>

&ensp;[<kbd> <br> Overview <br> </kbd>](#overview)&ensp;
&ensp;[<kbd> <br> Technologies <br> </kbd>](#technologies)&ensp;
&ensp;[<kbd> <br> Deploy <br> </kbd>](#deploy)&ensp;
<br><br><br><br></div>

## Table of Contents
- [De Bias](#de-bias)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Technologies](#technologies)
  - [Deploy](#deploy)
    - [Port Mapping](#port-mapping)
    - [Using external S3 provider](#using-external-s3-provider)
    - [Using local S3 provider](#using-local-s3-provider)
    - [Remove services](#remove-services)


## Overview

WIP

## Technologies

WIP

## Deploy

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