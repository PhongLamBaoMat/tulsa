from collections.abc import AsyncIterator
from datetime import datetime
from time import mktime
from typing import override
from urllib.parse import urljoin

from crawlee import Request
from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog


async def default_request_handler(
    context: ParselCrawlingContext,
) -> AsyncIterator[Blog]:
    item = Blog.from_html_selector(context.selector)
    if not item:
        context.log.error(f"{context.request.url} | Cannt find the HTML element.")
        return

    published = (
        context.selector.xpath(
            '//div[@class="mantine-Text-root mantine-1rdqprb"]/text()'
        ).get()
        if not item.published
        else None
    )

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
                '//a[@class="CardBlogPost_link__ejiEr"]/@href'
            ).getall()
        ]
    )


class GendigitalSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=default_request_handler)
        self.router._handlers_by_label["fetch_articles"] = fetch_articles  # pyright: ignore [reportPrivateUsage]

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                Request.from_url(
                    "https://www.gendigital.com/blog/insights/research",
                    label="fetch_articles",
                ),
                Request.from_url(
                    "https://www.gendigital.com/blog/insights/reports",
                    label="fetch_articles",
                ),
            ]
        )
