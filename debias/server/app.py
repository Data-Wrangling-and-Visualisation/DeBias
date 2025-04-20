import datetime
import os

import litestar as lt
import msgspec as ms
import polars as pl
from litestar import Litestar

from debias.server.config import Config

envs = {}
for key, value in os.environ.items():
    envs[key.lower()] = value

Config.model_config["toml_file"] = os.environ.get("config", "config.toml")

config = Config()  # type: ignore


class Target(ms.Struct):
    id: str
    name: str
    main_page: str
    country: str
    alignment: str


@lt.get("/targets", sync_to_thread=False)
def get_targets(
    country: str | None = None,
    alignment: str | None = None,
) -> list[Target]:
    df = pl.read_database_uri(
        query="select * from targets",
        uri=config.pg.connection,
    ).lazy()

    if country is not None:
        df = df.filter(pl.col("country") == country)

    if alignment is not None:
        df = df.filter(pl.col("alignment") == alignment)

    return [ms.json.decode(x, type=Target) for x in df.collect().to_dicts()]  # type: ignore


@lt.get("/keywords", sync_to_thread=False)
def get_keywords(
    date: datetime.date | None = None, country: str | None = None, alignment: str | None = None
) -> list[dict]:
    df = pl.read_database_uri(
        query="""select
            k.id as keyword_id,
            k.type as keyword_type,
            k.keyword,
            k.count as keyword_count,
            d.id as document_id,
            d.absolute_url as document_url,
            d.title as document_title,
            d.snippet as document_snippet,
            d.article_datetime as document_datetime,
            t.id as target_id,
            t.name as target_name,
            t.main_page as target_main_page,
            t.country as target_country,
            t.alignment as target_alignment
        from keyword_appearances as ka
        join keywords as k on k.id = ka.keyword_id
        join documents as d on d.id = ka.document_id
        join targets as t on t.id = d.target_id
        """,
        uri=config.pg.connection,
    ).lazy()

    if date is not None:
        df = df.filter(pl.col("document_datetime").dt.date() == date)

    if country is not None:
        df = df.filter(pl.col("target_country") == country)

    if alignment is not None:
        df = df.filter(pl.col("target_alignment") == alignment)

    result = (
        df.with_columns(pl.col("document_datetime").dt.date().alias("date"))
        .group_by(["keyword_type", "keyword", "date"])
        .agg(
            pl.len().alias("count"),
            pl.struct(
                pl.col("document_id").alias("id"),
                pl.col("document_title").alias("title"),
                pl.col("target_alignment").alias("alignment"),
                pl.col("document_snippet").alias("snippet"),
                pl.col("target_country").alias("country"),
            ).alias("mentioned_in"),
        )
        .group_by(["keyword_type", "keyword"])
        .agg(
            pl.sum("count").alias("total_count"),
            pl.struct(pl.col("date").cast(pl.Utf8), pl.col("count"), pl.col("mentioned_in")).alias("buckets"),
        )
        .with_columns(pl.struct(pl.col("keyword").alias("text"), pl.col("keyword_type").alias("type")).alias("keyword"))
        .select(["keyword", "total_count", "buckets"])
        .collect()
        .to_dicts()
    )

    return result


@lt.get("/topics", sync_to_thread=False)
def get_topics(
    date: datetime.date | None = None, country: str | None = None, alignment: str | None = None
) -> list[dict]:
    df = pl.read_database_uri(
        query="""select
            t.id as topic_id,
            t.type as topic_type,
            t.topic,
            t.count as topic_count,
            d.id as document_id,
            d.absolute_url as document_url,
            d.title as document_title,
            d.snippet as document_snippet,
            d.article_datetime as document_datetime,
            tg.id as target_id,
            tg.name as target_name,
            tg.main_page as target_main_page,
            tg.country as target_country,
            tg.alignment as target_alignment
        from topic_appearances as ta
        join topics as t on t.id = ta.topic_id
        join documents as d on d.id = ta.document_id
        join targets as tg on tg.id = d.target_id
        """,
        uri=config.pg.connection,
    ).lazy()

    if date is not None:
        df = df.filter(pl.col("document_datetime").dt.date() == date)

    if country is not None:
        df = df.filter(pl.col("target_country") == country)

    if alignment is not None:
        df = df.filter(pl.col("target_alignment") == alignment)

    result = (
        df.with_columns(pl.col("document_datetime").dt.date().alias("date"))
        .group_by(["topic_type", "topic", "date"])
        .agg(
            pl.len().alias("count"),
            pl.struct(
                pl.col("document_id").alias("id"),
                pl.col("document_title").alias("title"),
                pl.col("document_snippet").alias("snippet"),
                pl.col("target_alignment").alias("alignment"),
                pl.col("target_country").alias("country"),
            ).alias("mentioned_in"),
        )
        .group_by(["topic_type", "topic"])
        .agg(
            pl.sum("count").alias("total_count"),
            pl.struct(pl.col("date").cast(pl.Utf8), pl.col("count"), pl.col("mentioned_in")).alias("buckets"),
        )
        .with_columns(pl.struct(pl.col("topic").alias("text"), pl.col("topic_type").alias("type")).alias("topic"))
        .select(["topic", "total_count", "buckets"])
        .collect()
        .to_dicts()
    )

    return result


app = Litestar(route_handlers=[get_targets, get_keywords, get_topics])
