from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime

import psycopg
from faststream import Logger


@dataclass
class Metadata:
    target_id: str
    target_name: str
    absolute_url: str
    last_scrape: datetime
    filepath: str
    url_hash: str
    content_hash: str
    content_size: int


class Metastore:
    def __init__(self, connection: str):
        self._conn_str = connection
        self._connection: psycopg.AsyncConnection | None = None

    async def init(self, logger: Logger):
        conn = await self._get_connection(logger)
        async with conn.cursor() as cur:
            logger.info("creating if metadata table if not exists")
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS public.metadata (
                    id BIGSERIAL PRIMARY KEY,
                    target_id TEXT NOT NULL,
                    target_name TEXT NOT NULL,
                    absolute_url TEXT NOT NULL,
                    last_scrape TIMESTAMP NOT NULL,
                    filepath TEXT NOT NULL,
                    url_hash TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    content_size INTEGER NOT NULL
                );
            """)
            await conn.commit()

        logger.info("created metadata table")

    async def _get_connection(self, logger: Logger) -> psycopg.AsyncConnection:
        if self._connection is None or self._connection.closed:
            self._connection = await psycopg.AsyncConnection.connect(self._conn_str)
        logger.debug(f"connected to {self._connection.info}")
        return self._connection

    @asynccontextmanager
    async def with_transaction(self, logger: Logger):
        async with (await self._get_connection(logger)).transaction() as t:
            try:
                yield t
            except Exception as e:
                logger.error(f"transaction failed: {e}")
                raise e from e
            else:
                logger.debug("committing transaction")

    async def save_metadata(self, metadata: Metadata, logger: Logger) -> int:
        conn = await self._get_connection(logger)
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO public.metadata (
                    target_id, target_name, absolute_url, last_scrape,
                    filepath, url_hash, content_hash, content_size
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """,
                (
                    metadata.target_id,
                    metadata.target_name,
                    metadata.absolute_url,
                    metadata.last_scrape,
                    metadata.filepath,
                    metadata.url_hash,
                    metadata.content_hash,
                    metadata.content_size,
                ),
            )
            result = await cur.fetchone()
            logger.info(f"saved metadata: {result}")
            return result[0]  # type: ignore
