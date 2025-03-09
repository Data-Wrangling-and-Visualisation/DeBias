# De Bias

<div align = center><img src=".github/assets/banner.png"><br><br>

&ensp;[<kbd> <br> Overview <br> </kbd>](#overview)&ensp;
&ensp;[<kbd> <br> Technologies <br> </kbd>](#technologies)&ensp;
&ensp;[<kbd> <br> Deploy <br> </kbd>](#deploy)&ensp;
&ensp;[<kbd> <br> Current state <br> </kbd>](#current-state)&ensp;
<br><br><br><br></div>

## Overview

The repository is dedicated to the Debias project, dedicated to showing relationships between different concepts in the news. 

We cover different geographical locations (mainly USA and UK), different political positions (taken from [AllSides](https://www.allsides.com/unbiased-balanced-news)) and varios news providers.

The final goal is to create an interactive visualization, which would show how concepts are interconnected within different time stamps and from different points of view.

## Technologies

### Experiments
- Python <img src=".github/assets/Python-logo-notext.svg.png" width="40"></img>

### Data Scraping
- Docker <img src=".github/assets/4373190_docker_logo_logos_icon.png" width="40"></img>
- Go <img src=".github/assets/Go-Logo_Blue.png" width="40"></img>
- Colly <img src=".github/assets/colly.png" width="40"></img>
- Redis <img src=".github/assets/redis.svg" width="40"></img>
- Minio <img src=".github/assets/minio-1.svg" width="20"></img>
- MongoDB <img src=".github/assets/mongodb-icon-1.svg" width="40"></img>

## Deploy

WIP

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
