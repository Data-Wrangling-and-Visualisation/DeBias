# De Bias - scraper

## Prerequisites

- [uv](https://github.com/astral-sh/uv)
- [nats](https://github.com/nats-io/nats-server)

## Development

1. Create `config.toml` file in the `debias/scraper` directory

2. Install dependencies:
```bash
uv sync --group scraper
```

3. Launch application:
```bash
uv run faststream run debias.scraper:app --config=debias/scraper/config.toml --workers 1
```
