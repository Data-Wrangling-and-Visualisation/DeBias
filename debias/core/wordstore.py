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
    title: str
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
        logger.info("initializing wordstore")

        async with (await self._get_connection()).cursor() as conn:
            logger.info("creating table targets")
            await conn.execute("""
                create table if not exists targets (
                    id text not null primary key,
                    name text not null,
                    main_page text not null,
                    country text not null,
                    alignment text not null
                );
            """)
            logger.info("inserting into table targets")
            await conn.execute("""
                insert into targets (id, name, main_page, country, alignment) values
                    ('SKY','Sky News','https://news.sky.com/','UK','Lean Left'),
                    ('GBN','GBN','https://www.gbnews.com/','UK','Lean Right'),
                    ('ABC','ABC News','http://abcnews.go.com/','USA','Lean Left'),
                    ('DMU','Daily Mail','https://www.dailymail.co.uk/home/index.html','UK','Right'),
                    ('TIM','The Times','https://www.thetimes.com/','UK','Center'),
                    ('MIR','The Mirror','https://www.mirror.co.uk/','UK','Left'),
                    ('MET','Metro','https://metro.co.uk/','UK','Lean Left'),
                    ('STD','The Standard','https://www.standard.co.uk/','UK','Center'),
                    ('WAL','Wales Online','https://www.walesonline.co.uk/','UK','Lean Left'),
                    ('SUN','The Sun','https://www.thesun.co.uk/','UK','Center'),
                    ('GRD','The Guardian','https://www.theguardian.com/uk-news','UK','Left'),
                    ('BBC','BBC News','http://www.bbc.com/','UK','Center'),
                    ('BLB','Bloomberg','http://www.bloomberg.com/','USA','Lean Left'),
                    ('BUS','Business Insider','https://www.insider.com/','USA','Lean Left'),
                    ('BFN','BuzzFeed News','https://www.buzzfeednews.com','USA','Left'),
                    ('CBS','CBS News','https://www.cbsnews.com','USA','Lean Left'),
                    ('CNN','CNN Digital','https://cnn.com','USA','Lean Left'),
                    ('FRB','Forbes','https://www.forbes.com','USA','Center'),
                    ('FND','Fox News Digital','http://www.foxnews.com/','USA','Right'),
                    ('NRN','National Review','https://www.nationalreview.com/news/','USA','Lean Right'),
                    ('NBC','NBC News Digital','https://www.nbcnews.com','USA','Lean Left'),
                    ('NYP','New York Post (News)','https://nypost.com','USA','Lean Right'),
                    ('NYT','New York Times (News)','https://www.nytimes.com','USA','Lean Left'),
                    ('NNN','NewsNation','https://www.newsnationnow.com','USA','Center'),
                    ('SPC','The American Spectator','https://spectator.org','USA','Right'),
                    ('ATL','The Atlantic','https://www.theatlantic.com/world/','USA','Left'),
                    ('DWN','The Daily Wire','https://www.dailywire.com','USA','Right'),
                    ('ECO','The Economist','https://www.economist.com','USA','Lean Left'),
                    ('FED','The Federalist','https://thefederalist.com','USA','Right'),
                    ('NYK','The New Yorker','https://www.newyorker.com','USA','Left'),
                    ('TIM','Time Magazine','https://time.com','USA','Lean Left'),
                    ('UTN','USA TODAY','https://www.usatoday.com','USA','Lean Left'),
                    ('VOX','Vox','https://www.vox.com','USA','Left'),
                    ('WSJ','Wall Street Journal (News)','https://www.wsj.com','USA','Center'),
                    ('WEN','Washington Examiner','https://washingtonexaminer.com','USA','Lean Right'),
                    ('WFB','Washington Free Beacon','https://freebeacon.com','USA','Right'),
                    ('WPN','Washington Post','https://www.washingtonpost.com','USA','Lean Left'),
                    ('WTN','Washington Times','https://www.washingtontimes.com','USA','Lean Right')
                on conflict (id) do nothing;
            """)
            logger.info("inserting into table documents")
            await conn.execute("""
                create table if not exists documents (
                    id serial primary key,
                    title text not null,
                    absolute_url text not null,
                    url_hash text not null,
                    target_id text not null references targets(id),
                    scrape_datetime timestamp not null,
                    article_datetime timestamp,
                    snippet text not null
                );               
            """)
            logger.info("inserting into table keywords")
            await conn.execute("""
                create table if not exists keywords (
                    id serial primary key,
                    type text not null,
                    keyword text not null,
                    count int not null
                );
            """)
            await conn.execute("""
                create unique index if not exists keywords_type_keyword
                    on keywords(type, keyword);
            """)
            logger.info("inserting into table topics")
            await conn.execute("""
                create table if not exists topics (
                    id serial primary key,
                    type text not null,
                    topic text not null,
                    count int not null
                );
            """)
            await conn.execute(
                """
                create unique index if not exists topics_type_topic
                    on topics(type, topic);
            """
            )
            logger.info("inserting into table keyword_appearances")
            await conn.execute("""
                create table if not exists keyword_appearances (
                    keyword_id int references keywords(id),
                    document_id int references documents(id),
                    count int,
                    primary key (keyword_id, document_id)
                );
            """)
            logger.info("inserting into table topic_appearances")
            await conn.execute("""
                create table if not exists topic_appearances (
                    topic_id int references topics(id),
                    document_id int references documents(id),
                    count int,
                    primary key (topic_id, document_id)
                );
            """)

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
        async with self.with_transaction():
            async with (await self._get_connection()).cursor() as c:
                insert_document = psycopg.sql.SQL("""
                    insert into documents (title, absolute_url, url_hash, target_id, scrape_datetime, article_datetime, snippet)
                    values (%s, %s, %s, %s, %s, %s, %s)
                    returning id;
                """)
                r = await (
                    await c.execute(
                        insert_document,
                        (
                            result.title,
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
