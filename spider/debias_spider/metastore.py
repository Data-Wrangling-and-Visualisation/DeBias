from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from datetime import datetime

import psycopg


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

    async def init(self):
        conn = await self._get_connection()
        async with conn.cursor() as cur:
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
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

    async def _get_connection(self) -> psycopg.AsyncConnection:
        if self._connection is None or self._connection.closed:
            self._connection = await psycopg.AsyncConnection.connect(self._conn_str)
        return self._connection

    async def with_transaction(self) -> AbstractAsyncContextManager[psycopg.AsyncTransaction, None]:
        return (await self._get_connection()).transaction()  # type: ignore

    async def save_metadata(self, metadata: Metadata) -> int:
        conn = await self._get_connection()
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO metadata (
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
            return result[0]  # type: ignore
