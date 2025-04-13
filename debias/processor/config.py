import importlib.metadata
from typing import ClassVar, override

from core.configs import NatsConfig, PostgresConfig, S3Config
from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)


class Config(BaseSettings):
    nats: NatsConfig = Field(default_factory=NatsConfig, description="NATS configuration")
    s3: S3Config = Field(description="S3 configuration")
    pg: PostgresConfig = Field(description="PostgreSQL configuration")

    @property
    def version(self) -> str:
        return importlib.metadata.version("debias")

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        # look for enviroment variabled prefixed with `processor.` (case-insensitive). e.g. processor.log.level = debug
        env_prefix="processor.",
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
