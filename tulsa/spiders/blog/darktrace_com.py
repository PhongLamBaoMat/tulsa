import json
from collections.abc import AsyncIterator
from datetime import datetime
from time import mktime
from typing import override
from urllib.parse import urljoin

from crawlee import Request
from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import HtmlSpider
from tulsa.helpers import parse_date
from tulsa.models import Blog, Category


async def default_request_handler(
    context: ParselCrawlingContext,
) -> AsyncIterator[Blog]:
    for text in context.selector.xpath(
        '//script[@type="application/ld+json"]/text()'
    ).getall():
        entry = json.loads(text)
        if entry.get("@type", "") != "BlogPosting":
            continue
        title = entry["headline"]
        url = context.request.loaded_url or context.request.url
        description = entry.get("description")
        thumbnail = entry.get("image")
        published = entry.get("datePublished")

        item = Blog(url=url, title=title, category=Category.Generic)
        if description:
            item.description = description
        if thumbnail:
            item.thumbnail = thumbnail
        if published:
            published = parse_date(published)
            if published:
                item.published = datetime.fromtimestamp(mktime(published))

        yield item


async def fetch_articles(context: ParselCrawlingContext):
    _ = await context.add_requests(
        [
            Request.from_url(
                urljoin(context.request.loaded_url or context.request.url, url)
            )
            for url in context.selector.xpath(
                '//div[@class="soc-all-posts w-dyn-items"]/div[@role="listitem"]/a[@class="soc-item_inner w-inline-block"]/@href'
            ).getall()[:20]
        ]
    )


class DarktraceSpider(HtmlSpider):
    def __init__(self):
        super().__init__(default_request_handler=default_request_handler)
        self.router._handlers_by_label["fetch_articles"] = fetch_articles  # pyright: ignore [reportPrivateUsage]

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                Request.from_url(
                    "https://www.darktrace.com/inside-the-soc", label="fetch_articles"
                )
            ]
        )
