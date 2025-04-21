# De Bias - renderer


## Prerequisites

- [uv](https://github.com/astral-sh/uv)
- [nats](https://github.com/nats-io/nats-server)
- [playwright](https://playwright.dev/)

## Development

1. Create `config.toml` file in the `debias/renderer` directory

2. Install dependencies:
```bash
uv sync --group renderer
```
3. Launch application:
```bash
uv run faststream run debias.renderer:app --config=debias/renderer/config.toml --workers 1
```
