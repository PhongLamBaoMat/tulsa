from typing import override
from urllib.parse import urljoin

from crawlee import Request
from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.models import Blog


async def default_request_handler(context: ParselCrawlingContext):
    item = Blog.from_html_selector(context.selector)
    if not item:
        context.log.error(
            f"{context.request.url} | Cannot find url or title HTML element"
        )
        return

    yield item


async def fetch_articles(context: ParselCrawlingContext):
    await context.add_requests(
        [
            Request.from_url(
                urljoin(context.request.loaded_url or context.request.url, url)
            )
            for url in context.selector.xpath(
                '//div[@class="grid grid-cols-1 gap-10 duration-150 sm:grid-cols-2 md:grid-cols-3 lg:gap-16"]/a/@href'
            ).getall()
        ]
    )


class ClarotyComSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=default_request_handler)
        self.router._handlers_by_label["fetch_articles"] = fetch_articles  # pyright: ignore [reportPrivateUsage]

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                Request.from_url(
                    "https://claroty.com/team82/research", label="fetch_articles"
                )
            ]
        )
