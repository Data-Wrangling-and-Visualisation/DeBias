import importlib.metadata
from typing import ClassVar, Literal, override

from core.configs import HttpConfig, NatsConfig, PostgresConfig, S3Config
from pydantic import BaseModel, Field, HttpUrl
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)


class TargetConfig(BaseModel):
    id: str = Field(description="ID of the target")
    name: str = Field(description="Human-readable name of the target")
    root: HttpUrl = Field(description="Root URL of the target")
    domain_only: bool = Field(default=True, description="Whether to visit links on other domains")
    render: Literal["auto", "always", "never"] = Field(
        default="auto",
        description="""Whether the webpase need rendering.
        Default is 'auto' which would determine  based on the first request content."
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


class AppConfig(BaseModel):
    targets: list[TargetConfig] = Field(default_factory=list, description="Targets configuration")


class KeyValueConfig(BaseModel):
    dsn: str = Field(description="Redis DSN")


class Config(BaseSettings):
    nats: NatsConfig = Field(default_factory=NatsConfig, description="NATS configuration")
    http: HttpConfig = Field(default_factory=HttpConfig, description="HTTP configuration")
    app: AppConfig = Field(default_factory=AppConfig, description="Application configuration")
    s3: S3Config = Field(description="S3 configuration")
    pg: PostgresConfig = Field(description="PostgreSQL configuration")
    keyvalue: KeyValueConfig = Field(description="Key-Value configuration")

    @property
    def version(self) -> str:
        return importlib.metadata.version("debias_scraper")

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        # look for enviroment variabled prefixed with `scraper.` (case-insensitive). e.g. scraper.log.level = debug
        env_prefix="scraper.",
        case_sensitive=False,
        env_nested_delimiter=".",
        # if .env file is present - load it
        env_file=".env",
        env_file_encoding="utf-8",
        # ignore additional fields stated in configuration file (do not load them to memory for security)
        extra="ignore",
    )

    @classmethod
    @override
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            # top priority - arguments which are passed to init function
            init_settings,
            # then we try to load from environment variables
            env_settings,
            # then we try to load from dotenv file
            dotenv_settings,
            # then we try to load from toml config
            TomlConfigSettingsSource(settings_cls),
            # then we try to load from file secret
            file_secret_settings,
        )
