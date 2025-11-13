from collections.abc import AsyncIterator
from datetime import datetime
from time import mktime
from typing import cast, override
from urllib.parse import urljoin

from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog, Category


async def default_request_handler(
    context: ParselCrawlingContext,
) -> AsyncIterator[Blog]:
    items = context.selector.xpath("//article")
    if len(items) == 0:
        raise ValueError(f"Cannot find HTLM elements: {context.request.url}")

    for entry in items:
        title = cast(str, entry.xpath(".//h2/a/text()").get()).strip()
        url = cast(str, entry.xpath(".//h2/a/@href").get()).strip()
        published = cast(str, entry.xpath(".//time/text()").get()).strip()
        item = Blog(
            url=urljoin(context.request.loaded_url or context.request.url, url),
            title=title,
            category=Category.Generic,
        )
        published = parse_date(published)
        if published:
            published = datetime.fromtimestamp(mktime(published))
            item.published = published

        yield item


class Verses21Spider(Spider):
    def __init__(
        self,
    ) -> None:
        super().__init__(default_request_handler=default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(["https://21verses.blog/"])
