from pydantic import BaseModel, Field, NatsDsn


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
