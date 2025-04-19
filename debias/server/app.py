import datetime
import os
from typing import Literal

import litestar as lt
import msgspec as ms
import polars as pl
from litestar import Litestar

from debias.server.config import Config

envs = {}
for key, value in os.environ.items():
    envs[key.lower()] = value

Config.model_config["toml_file"] = os.environ["server.config"]

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
    group: Literal["country", "alignment"] | None = None,
    date: datetime.date | None = None,
    country: str | None = None,
    alignment: str | None = None,
) -> list[dict]:
    df = pl.read_database_uri(
        query="""select
            k.type as keyword_type,
            k.keyword,
            k.count as keyword_count,
            d.id as document_id,
            d.absolute_url as document_url,
            d.title as document_title,
            d.snippet as document_snippet,
            d.article_datetime as document_datetime,
            d.id as document_id,
            t.id as target_id,
            t.name as target_name,
            t.main_page as target_main_page,
            t.country as target_country,
            t.alignment as target_alignment
        from keyword_appearances as ka
        join keywords as k on k.id = ka.keyword_id
        join documents as d on d.id = ka.document_id
        join targets as t on t.id = d.target_id;
        """,
        uri=config.pg.connection,
    ).lazy()

    if date is not None:
        df = df.filter(pl.col("document_datetime").dt.date() == date)

    if country is not None:
        df = df.filter(pl.col("target_country") == country)

    if alignment is not None:
        df = df.filter(pl.col("target_alignment") == alignment)

    df = (
        df.group_by(pl.col("keyword_type"), pl.col("keyword"))
        .agg(
            pl.struct(pl.col("keyword").alias("text"), pl.col("keyword_type").alias("type")).alias("keyword"),
            pl.len().alias("total_count"),
        )
        .group_by(pl.col("document_datetime").dt.date())
        .agg(
            pl.col("document_datetime").dt.date().alias("date"),
            pl.len().alias("count"),
            pl.col("mentioned_in").list.eval(
                pl.struct(
                    pl.element().struct.field("document_id").alias("id"),
                    pl.element().struct.field("document_title").alias("title"),
                    pl.element().struct.field("target_alignment").alias("alignment"),
                    pl.element().struct.field("target_country").alias("country"),
                ),
            ),
        )
    )

    return df.collect().to_dicts()


app = Litestar(route_handlers=[get_targets, get_keywords])
