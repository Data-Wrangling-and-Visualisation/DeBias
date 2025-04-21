FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS python3

RUN apt update && apt upgrade -y && apt install -y build-essential curl libpq-dev

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-group dev --group processor

RUN uv run python3 -c "import nltk; nltk.download('stopwords')"
RUN uv run python3 -c "import nltk; nltk.download('wordnet')"
RUN uv run python3 -c "import nltk; nltk.download('punkt')"

ADD . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-group dev --group processor

ENV PATH="/app/.venv/bin:$PATH"
ENTRYPOINT []
