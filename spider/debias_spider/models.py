from datetime import datetime

from pydantic import BaseModel, Field


class FetchRequest(BaseModel):
    target_id: str = Field(description="ID of the target")
    url: str = Field(description="URL to fetch")


class ProcessRequest(BaseModel):
    url: str
    target_id: str
    filepath: str
    metadata: int
    datetime: datetime


class RenderRequest(BaseModel):
    target_id: str
    url: str
