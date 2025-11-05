from __future__ import annotations

from datetime import datetime
from time import mktime
from typing import Annotated

from parsel.selector import Selector
from pydantic import BaseModel, Field
from pydantic.config import ConfigDict
from pydantic.functional_validators import field_validator

from tulsa.helpers import is_valid_url, parse_date
from tulsa.models.category import Category


class Blog(BaseModel):
    url: Annotated[str, Field(init=True, serialization_alias="_id")]
    title: Annotated[str, Field(init=True)]
    category: Annotated[Category, Field()] = Category.Generic
    author: Annotated[str | None, Field()] = None
    description: Annotated[str | None, Field()] = None
    published: Annotated[datetime | None, Field()] = None
    thumbnail: Annotated[str | None, Field()] = None
    sent: Annotated[bool, Field()] = False

    model_config = ConfigDict(validate_assignment=True)  # pyright: ignore [reportUnannotatedClassAttribute]

    @field_validator("url", "thumbnail")
    @classmethod
    def ensure_url(cls, v: str | None):
        if not v or is_valid_url(v):
            return v
        raise ValueError("Not a URL")

    @staticmethod
    def from_html_selector(selector: Selector) -> Blog | None:
        title = selector.xpath('//head/meta[@property="og:title"]/@content').get()
        if not title:
            return None
        url = (
            selector.xpath('//head/meta[@property="og:url"]/@content').get()
            or selector.xpath('//head/link[@rel="canonical"]/@href').get()
        )
        if not url:
            return None
        description = selector.xpath(
            '//head/meta[@property="og:description"]/@content'
        ).get()
        thumbnail = selector.xpath('//head/meta[@property="og:image"]/@content').get()
        # TODO: published has more property names
        published = selector.xpath(
            '//head/meta[@property="article:published_time"]/@content'
        ).get()
        item = Blog(url=url, title=title)
        if description:
            item.description = description
        if thumbnail:
            item.thumbnail = thumbnail
        if published:
            published = parse_date(published)
            if published:
                item.published = datetime.fromtimestamp(mktime(published))

        return item
