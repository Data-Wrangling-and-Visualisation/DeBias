from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, NatsDsn


class NatsConfig(BaseModel):
    dsn: NatsDsn = Field(
        default_factory=lambda: NatsDsn("nats://localhost:4222"),
        description="Domain Service Name (DSN) of the NATS server",
    )


class HttpConfig(BaseModel):
    user_agent: str = Field(default="debias-scraper", description="User agent string")


class S3Config(BaseModel):
    access_key: str = Field(description="Access key for S3")
    secret_key: str = Field(description="Secret key for S3")
    endpoint: str = Field(description="Endpoint for S3")
    bucket_name: str = Field(description="Bucket name for S3")
    region: str = Field(description="Region for S3")


class PostgresConfig(BaseModel):
    connection: str = Field(description="Connection string for PostgreSQL")


class TargetConfig(BaseModel):
    id: str = Field(description="ID of the target")
    name: str = Field(description="Human-readable name of the target")
    root: HttpUrl = Field(description="Root URL of the target")
    domain_only: bool = Field(default=True, description="Whether to visit links on other domains")
    render: Literal["auto", "always", "never"] = Field(
        default="auto",
        description="""Whether the webpage needs rendering.
        Default is 'auto' which would determine based on the first request content."
        Other options are 'always' and 'never'.
        """,
    )
    text_selector: str = Field(
        default="",
        description="""Selector to find the text content of the target.
        Default is '' which would not find any text content.
        """,
    )
    href_selector: str = Field(
        default="a[href]",
        description="""Selector to find the link to the target.
        Default is 'a[href]' which would find all links.
        """,
    )
