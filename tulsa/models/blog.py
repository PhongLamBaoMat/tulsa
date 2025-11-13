from __future__ import annotations

from datetime import datetime
from time import mktime
from typing import Annotated, Any

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
        author = selector.xpath('//head/meta[@name="author"]/@content').get()
        item = Blog(url=url, title=title)
        if description:
            item.description = description
        if thumbnail:
            item.thumbnail = thumbnail
        if author:
            item.author = author
        if published:
            published = parse_date(published)
            if published:
                item.published = datetime.fromtimestamp(mktime(published))

        return item

    @staticmethod
    def from_json_schema(obj: dict[str, Any]) -> Blog | None:
        """
        Current supports "SocialMediaPosting", "Article"
        """
        title = None
        url = None
        description = None
        thumbnail = None
        published = None
        author = None

        if obj.get("@type") == "SocialMediaPosting":
            title = obj["headline"]
            url = obj["url"]
            description = obj["description"]
            thumbnail = obj["image"][0] if len(obj.get("image", [])) > 0 else None
            published = parse_date(obj["datePublished"])
            if obj.get("author") and obj["author"].get("name"):
                author = obj["author"]["name"]
        elif obj.get("@type") == "Article":
            title = obj["name"]
            url = obj["url"]
            description = obj["description"]
            published = parse_date(obj["datePublished"])
            if obj.get("author") and obj["author"].get("name"):
                author = obj["author"]["name"]
        elif obj.get("@type") == "WebSite":
            title = obj["headline"]
            url = obj["url"]
            description = obj["description"]
            thumbnail = (
                obj["image"]["url"]
                if obj.get("image") and obj["image"].get("url")
                else None
            )
            published = parse_date(obj["datePublished"])

        if not url or not title:
            return None

        item = Blog(url=url, title=title)
        if description:
            item.description = description
        if author:
            item.author = author
        if thumbnail:
            item.thumbnail = thumbnail
        if published:
            item.published = datetime.fromtimestamp(mktime(published))

        return item
