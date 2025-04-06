from datetime import datetime

from pydantic import BaseModel, Field


class FetchRequest(BaseModel):
    url: str = Field(description="URL to fetch")


class ProcessRequest(BaseModel):
    url: str
    target_id: str
    filepath: str
    metadata: int
    datetime: datetime


class RenderRequest(BaseModel):
    url: str
