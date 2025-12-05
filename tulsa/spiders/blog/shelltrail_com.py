from typing import override
from urllib.parse import urljoin

from crawlee import Request
from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.models import Blog


class ShelltrailComSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)
        self.router._handlers_by_label["fetch_articles"] = self.fetch_articles  # pyright: ignore [reportPrivateUsage]

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                Request.from_url(
                    "https://shelltrail.com/research", label="fetch_articles"
                )
            ]
        )

    @staticmethod
    async def fetch_articles(context: ParselCrawlingContext):
        items = context.selector.xpath(
            '//ul[@class="mt-12 grid md:grid-cols-2 gap-8"]/li/a/@href'
        ).getall()

        if len(items) == 0:
            context.log.error(f"{context.request.url} | Cannot find HTML element")
            return

        await context.add_requests(
            [
                Request.from_url(
                    urljoin(context.request.loaded_url or context.request.url, url)
                )
                for url in items
            ]
        )

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        item = Blog.from_html_selector(context.selector)
        if not item:
            context.log.error(
                f"{context.request.url} | Cannot find url or title HTML element"
            )
            return
        item.title = item.title.removesuffix(" | Shelltrail")
        yield item
