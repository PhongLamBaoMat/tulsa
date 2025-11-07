from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from tulsa.models.category import Category, Severity


class HacktivityBounty(BaseModel):
    url: Annotated[str, Field(init=True, serialization_alias="_id")]
    title: Annotated[str, Field(init=True)]
    category: Annotated[Category, Field(init=True)] = Category.HacktivityBounty
    reporter: Annotated[str | None, Field()] = None
    program: Annotated[str | None, Field()] = None
    description: Annotated[str | None, Field()] = None
    severity: Annotated[Severity | None, Field()] = None
    awarded: Annotated[float | None, Field()] = None
    published: Annotated[datetime | None, Field()] = None
    sent: Annotated[bool, Field()] = False
