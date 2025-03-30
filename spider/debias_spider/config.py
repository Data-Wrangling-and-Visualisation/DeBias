import importlib.metadata
from typing import ClassVar, override

from pydantic import BaseModel, Field, NatsDsn
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


class Config(BaseSettings):
    nats: NatsConfig = Field(default_factory=NatsConfig, description="NATS configuration")
    http: HttpConfig = Field(default_factory=HttpConfig, description="HTTP configuration")

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
