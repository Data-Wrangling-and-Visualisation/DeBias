# De Bias - server

## Prerequisites

- [uv](https://github.com/astral-sh/uv)
- [postgresql](https://www.postgresql.org/)

## Development

1. Create `config.toml` file in the `debias/server` directory

2. Install dependencies:
```bash
uv sync --group server
```
3. Development launch:
```bash
CONFIG=config.toml uv run litestar --app debias.server:app run --debug --reload
```
4. Production launch:
```bash
uv run litestar --app debias.server:app run --host 0.0.0.0 --port 8080
```

## Process

Server retrieves data from the tables, defined in `wordstore` service, and aggregates it. Then it serves the data to the client to be rendered. Server also serves the frontend files as well.