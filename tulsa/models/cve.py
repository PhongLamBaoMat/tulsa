from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class Cve(BaseModel):
    id: Annotated[str, Field(init=True, serialization_alias="_id")]
    url: Annotated[str, Field(init=True)]
    published: Annotated[datetime, Field(init=True)]
    description: Annotated[str | None, Field()] = None
    score: Annotated[float, Field()] = 0.0
    cna: Annotated[str | None, Field()] = None
    sent: Annotated[bool, Field()] = False
