# De Bias - Spider

## Prerequisites

- [uv](https://github.com/astral-sh/uv)
- [nats](https://github.com/nats-io/nats-server)

## Development

Install dependencies:
```bash
uv sync
```

Launch application with hot reload:
```bash
uv run faststream run debias_spider:app --reload
```