import importlib.metadata
from typing import ClassVar, Literal, override

from pydantic import BaseModel, Field, HttpUrl, NatsDsn
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)


class NatsConfig(BaseModel):
    dsn: NatsDsn = Field(
        default_factory=lambda: NatsDsn("nats://localhost:4222"),
        description="Domain Service Name (DSN) of the NATS server",
    )


class HttpConfig(BaseModel):
    host: str = Field(default="0.0.0.0", description="Host address to bind application to")
    port: int = Field(default=8080, description="Port number to bind application to")


class TargetConfig(BaseModel):
    id: str = Field(description="ID of the target")
    name: str = Field(description="Human-readable name of the target")
    root: HttpUrl = Field(description="Root URL of the target")
    render: Literal["auto", "always", "never"] = Field(
        default="auto",
        description="""Whether the webpase need rendering.
        Default is 'auto' which would determine  based on the first request content."
        Other options are 'always' and 'never'.
        """,
    )
    selector: str = Field(
        default="a[href]",
        description="""Selector to find the link to the target.
        Default is 'a[href]' which would find all links.
        """,
    )


class AppConfig(BaseModel):
    targets: list[TargetConfig] = Field(default_factory=list, description="Targets configuration")


class Config(BaseSettings):
    nats: NatsConfig = Field(default_factory=NatsConfig, description="NATS configuration")
    http: HttpConfig = Field(default_factory=HttpConfig, description="HTTP configuration")
    app: AppConfig = Field(default_factory=AppConfig, description="Application configuration")

    @property
    def version(self) -> str:
        return importlib.metadata.version("debias_spider")

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        # look for enviroment variabled prefixed with `spider.` (case-insensitive). e.g. spider.log.level = debug
        env_prefix="spider.",
        case_sensitive=False,
        env_nested_delimiter=".",
        # if .env file is present - load it
        env_file=".env",
        env_file_encoding="utf-8",
        # look for config.toml file as main configuration file
        toml_file="config.toml",
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
