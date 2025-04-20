import datetime
import os

import litestar as lt
import msgspec as ms
import polars as pl
from litestar import Litestar
from litestar.config.cors import CORSConfig

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


@lt.get("/api/targets", sync_to_thread=False)
def get_targets(
    country: str | None = None,
    alignment: str | None = None,
) -> list[Target]:
    df = pl.read_database_uri(
        query="select * from targets",
        uri=config.pg.connection,
    ).lazy()

    if country is not None:
        df = df.filter(pl.col("country").is_in(country.split(";")))

    if alignment is not None:
        df = df.filter(pl.col("alignment").is_in(alignment.split(";")))

    return [ms.json.decode(x, type=Target) for x in df.collect().to_dicts()]  # type: ignore


@lt.get("/api/keywords", sync_to_thread=False)
def get_keywords(
    country: str | None = None,
    alignment: str | None = None,
    date_from: datetime.date | None = None,
    date_till: datetime.date | None = None,
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

    if date_from is not None:
        df = df.filter(pl.col("document_datetime").dt.date().ge(date_from))

    if date_till is not None:
        df = df.filter(pl.col("document_datetime").dt.date().le(date_till))

    if country is not None:
        df = df.filter(pl.col("target_country").is_in(country.split(";")))

    if alignment is not None:
        df = df.filter(pl.col("target_alignment").is_in(alignment.split(";")))

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


@lt.get("/api/topics", sync_to_thread=False)
def get_topics(
    date_from: datetime.date | None = None,
    date_till: datetime.date | None = None,
    country: str | None = None,
    alignment: str | None = None,
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

    if date_from is not None:
        df = df.filter(pl.col("document_datetime").dt.date().ge(date_from))

    if date_till is not None:
        df = df.filter(pl.col("document_datetime").dt.date().le(date_till))

    if country is not None:
        df = df.filter(pl.col("target_country").is_in(country.split(";")))

    if alignment is not None:
        df = df.filter(pl.col("target_alignment").is_in(alignment.split(";")))

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


@lt.get("/api/topics/graph", sync_to_thread=False)
def get_topics_graph(
    date_from: datetime.date | None = None,
    date_till: datetime.date | None = None,
    country: str | None = None,
    alignment: str | None = None,
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

    if date_from is not None:
        df = df.filter(pl.col("document_datetime").dt.date().ge(date_from))

    if date_till is not None:
        df = df.filter(pl.col("document_datetime").dt.date().le(date_till))

    if country is not None:
        df = df.filter(pl.col("target_country").is_in(country.split(";")))

    if alignment is not None:
        df = df.filter(pl.col("target_alignment").is_in(alignment.split(";")))

    topics_df = df.select(pl.col("topic_id"), pl.col("topic_type"), pl.col("topic"), pl.col("topic_count")).unique()

    mentioned_in_df = df.group_by("topic_id").agg(
        pl.struct(
            pl.col("document_id").alias("id"),
            pl.col("document_title").alias("title"),
            pl.col("document_snippet").alias("snippet"),
            pl.col("target_alignment").alias("alignment"),
            pl.col("target_country").alias("country"),
        ).alias("mentioned_in"),
    )

    doc_topic_df = df.select(pl.col("document_id"), pl.col("topic_id"), pl.col("topic_type"), pl.col("topic"))

    cooccurrences_df = (
        doc_topic_df.join(
            doc_topic_df.select(
                pl.col("document_id"),
                pl.col("topic_id").alias("topic_id_related"),
                pl.col("topic_type").alias("topic_type_related"),
                pl.col("topic").alias("topic_related"),
            ),
            on="document_id",
        )
        .filter(pl.col("topic_id") != pl.col("topic_id_related"))
        .group_by("topic_id", "topic_id_related", "topic_type_related", "topic_related")
        .agg(pl.count().alias("cooccurrence_count"))
    )

    related_topics_df = cooccurrences_df.group_by("topic_id").agg(
        pl.struct(
            pl.struct(
                pl.col("topic_type_related").alias("type"),
                pl.col("topic_related").alias("text"),
            ).alias("topic"),
            pl.col("cooccurrence_count"),
        ).alias("related")
    )

    result = (
        topics_df.join(related_topics_df, on="topic_id", how="left")
        .join(mentioned_in_df, on="topic_id", how="left")
        .select(
            pl.struct(
                pl.struct(
                    pl.col("topic_type").alias("type"),
                    pl.col("topic").alias("text"),
                    pl.col("topic_count").alias("total_count"),
                ).alias("topic"),
                pl.col("related").fill_null([]),
            ),
            pl.col("mentioned_in"),
        )
        .collect()
        .to_dicts()
    )

    return result


@lt.get("/api/keywords/graph", sync_to_thread=False)
def get_keywords_graph(
    date_from: datetime.date | None = None,
    date_till: datetime.date | None = None,
    country: str | None = None,
    alignment: str | None = None,
    topic: str | None = None,
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
            t.alignment as target_alignment,
            tp.topic as topic,
            tp.type as topic_type
        from keyword_appearances as ka
        join keywords as k on k.id = ka.keyword_id
        join documents as d on d.id = ka.document_id
        join targets as t on t.id = d.target_id
        join topic_appearances as ta on ta.document_id = d.id
        join topics as tp on tp.id = ta.topic_id
        """,
        uri=config.pg.connection,
    ).lazy()

    if date_from is not None:
        df = df.filter(pl.col("document_datetime").dt.date().ge(date_from))

    if date_till is not None:
        df = df.filter(pl.col("document_datetime").dt.date().le(date_till))

    if country is not None:
        df = df.filter(pl.col("target_country").is_in(country.split(";")))

    if alignment is not None:
        df = df.filter(pl.col("target_alignment").is_in(alignment.split(";")))

    if topic is not None:
        df = df.filter(pl.col("topic").is_in(topic.split(";")))

    keywords_df = df.select(
        pl.col("keyword_id"), pl.col("keyword_type"), pl.col("keyword"), pl.col("keyword_count")
    ).unique()

    topics_df = df.group_by("keyword_id").agg(
        pl.struct(
            pl.col("topic").alias("text"),
            pl.col("topic_type").alias("type"),
        )
        .alias("topics")
        .unique(),
    )

    mentioned_in_df = df.group_by("keyword_id").agg(
        pl.struct(
            pl.col("document_id").alias("id"),
            pl.col("document_title").alias("title"),
            pl.col("document_snippet").alias("snippet"),
            pl.col("target_alignment").alias("alignment"),
            pl.col("target_country").alias("country"),
        ).alias("mentioned_in"),
    )

    doc_keyword_df = df.select(pl.col("document_id"), pl.col("keyword_id"), pl.col("keyword_type"), pl.col("keyword"))

    cooccurrences_df = (
        doc_keyword_df.join(
            doc_keyword_df.select(
                pl.col("document_id"),
                pl.col("keyword_id").alias("keyword_id_related"),
                pl.col("keyword_type").alias("keyword_type_related"),
                pl.col("keyword").alias("keyword_related"),
            ),
            on="document_id",
        )
        .filter(pl.col("keyword_id") != pl.col("keyword_id_related"))
        .group_by("keyword_id", "keyword_id_related", "keyword_type_related", "keyword_related")
        .agg(pl.count().alias("cooccurrence_count"))
    )

    related_keywords_df = cooccurrences_df.group_by("keyword_id").agg(
        pl.struct(
            pl.struct(
                pl.col("keyword_type_related").alias("type"),
                pl.col("keyword_related").alias("text"),
            ).alias("keyword"),
            pl.col("cooccurrence_count"),
        ).alias("related")
    )

    result = (
        keywords_df.join(related_keywords_df, on="keyword_id", how="left")
        .join(mentioned_in_df, on="keyword_id", how="left")
        .join(topics_df, on="keyword_id", how="left")
        .select(
            pl.struct(
                pl.struct(
                    pl.col("keyword_type").alias("type"),
                    pl.col("keyword").alias("text"),
                    pl.col("keyword_count").alias("total_count"),
                ).alias("keyword"),
                pl.col("related").fill_null([]),
            ),
            pl.col("mentioned_in"),
            pl.col("topics"),
        )
        .collect()
        .to_dicts()
    )

    return result


app = Litestar(
    route_handlers=[get_targets, get_keywords, get_topics, get_topics_graph, get_keywords_graph],
    cors_config=CORSConfig(),
)
