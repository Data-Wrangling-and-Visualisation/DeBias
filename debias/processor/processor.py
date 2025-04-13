from datetime import datetime

from pydantic import BaseModel


class WebpageData(BaseModel):
    url: str
    """url of the fetch resource"""
    target_id: str
    """id of the target from the config"""
    filepath: str
    """filepath in s3 storage"""
    content: str
    """downloaded file content as string"""
    metadata: int
    """metadata id in metastore"""
    datetime: datetime
    """scraped at"""


def process_webpage(input: WebpageData):
    pass  # todo: implement
