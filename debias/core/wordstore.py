import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime

import psycopg
import psycopg.sql

logger = logging.getLogger(__name__)


@dataclass
class Keyword:
    text: str
    type: str


@dataclass
class Topic:
    text: str
    type: str


@dataclass
class ProcessingResult:
    absolute_url: str
    url_hash: str
    target_id: str
    scrape_datetime: datetime
    article_datetime: datetime
    snippet: str
    keywords: list[Keyword]
    topics: list[Topic]


@dataclass
class Target:
    id: str
    main_page: str
    country: str
    alignment: str


class Wordstore:
    def __init__(self, connection: str):
        self._conn_str = connection
        self._connection: psycopg.AsyncConnection | None = None

    async def _get_connection(self) -> psycopg.AsyncConnection:
        if self._connection is None or self._connection.closed:
            self._connection = await psycopg.AsyncConnection.connect(self._conn_str)
        logger.debug(f"connected to {self._connection.info}")
        return self._connection

    async def init(self):
        conn = await self._get_connection()
        await conn.execute("""
            create table if not exists targets (
                id text not null primary key,
                name text not null,
                main_page text not null,
                country text not null,
                alignment text not null
            );
        """)
        await conn.execute("""
            create table if not exists documents (
                id serial primary key,
                absolute_url text not null,
                url_hash text not null,
                target_id text not null references targets(id),
                scrape_datetime timestamp not null,
                article_datetime timestamp,
                snippet text not null,
            );                
        """)
        await conn.execute("""
            create table if not exists keywords (
                id serial primary key,
                type text not null,
                keyword text not null,
                count int not null
            );
        """)
        await conn.execute("""
            create unique index if not exist keywords_type_keyword
                on keywords(type, keyword);
        """)
        await conn.execute("""
            create table if not exists topics (
                id serial primary key,
                type text not null,
                topic text not null,
                count int not null
            );
        """)
        await conn.execute("""
            create table if not exists keyword_appearances (
                keyword_id int primary key references keywords(id),
                document_id int primary key references documents(id),
                count int
            );
        """)
        await conn.execute("""
            create table if not exists topic_appearances (
                topic_id int primary key references topics(id),
                document_id int primary key references documents(id),
                count int
            );
        """)

        await conn.close()

    @asynccontextmanager
    async def with_transaction(self):
        async with (await self._get_connection()).transaction() as t:
            try:
                yield t
            except Exception as e:
                logger.error(f"transaction failed: {e}")
                raise e from e
            else:
                logger.debug("committing transaction")

    async def save(self, result: ProcessingResult):
        async with self.with_transaction() as t:
            async with (await self._get_connection()).cursor() as c:
                insert_document = psycopg.sql.SQL("""
                    insert into documents (absolute_url, url_hash, target_id, scrape_datetime, article_datetime, snippet)
                    values (%s, %s, %s, %s, %s, %s)
                    returning id;
                """)
                r = await (
                    await c.execute(
                        insert_document,
                        (
                            result.absolute_url,
                            result.url_hash,
                            result.target_id,
                            result.scrape_datetime,
                            result.article_datetime,
                            result.snippet,
                        ),
                    )
                ).fetchone()
                if r is None:
                    raise ValueError(f"failed to insert document <{result.absolute_url}>")
                document_id = r[0]

                # create new keywords if not exists, update count if exists
                insert_keywords = psycopg.sql.SQL("""
                    insert into keywords (type, keyword, count) values (%s, %s, 1)
                    on conflict (type, keyword) do update set count = count + 1;
                    returning id;
                """)
                keyword_ids = []
                for keyword_id in result.keywords:
                    r = await (await c.execute(insert_keywords, (keyword_id.type, keyword_id.text))).fetchone()
                    if r is None:
                        raise ValueError(f"failed to insert keyword <{keyword_id.text}>")
                    keyword_ids.append(r[0])

                # create new topics if not exists, update count if exists
                insert_topics = psycopg.sql.SQL("""
                    insert into topics (type, topic, count) values (%s, %s, 1)
                    on conflict (type, topic) do update set count = count + 1;
                    returning id;
                """)
                topic_ids = []
                for topic in result.topics:
                    r = await (await c.execute(insert_topics, (topic.type, topic.text))).fetchone()
                    if r is None:
                        raise ValueError(f"failed to insert topic <{topic.text}>")
                    topic_ids.append(r[0])

                insert_keyword_appearances = psycopg.sql.SQL("""
                    insert into keyword_appearances (keyword_id, document_id, count)
                    values (%s, %s, 1)
                    on conflict (keyword_id, document_id) do update set count = count + 1;
                """)
                for keyword_id in keyword_ids:
                    await c.execute(insert_keyword_appearances, (keyword_id, document_id))

                insert_topic_appearances = psycopg.sql.SQL("""
                    insert into topic_appearances (topic_id, document_id, count)
                    values (%s, %s, 1)
                    on conflict (topic_id, document_id) do update set count = count + 1;
                """)
                for topic_id in topic_ids:
                    await c.execute(insert_topic_appearances, (topic_id, document_id))
