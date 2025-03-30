from typing import Literal

from pydantic import BaseModel, Field


class FetchRequest(BaseModel):
    target_id: str = Field(description="ID of the target")
    url: str = Field(description="URL to fetch")
    selector: str = Field(description="Selector to find the link to the target")
    render: Literal["auto", "always", "never"] = Field(
        default="auto",
        description="""Whether the webpase need rendering.
        Default is 'auto' which would determine  based on the first request content."
        Other options are 'always' and 'never'.
        """,
    )
