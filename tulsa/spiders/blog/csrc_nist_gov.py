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
            f"{context.request.url} | Cannot find title or url HTML element"
        )
        return

    context.log.info(item)
    yield item


async def fetch_articles(context: ParselCrawlingContext):
    items = context.selector.xpath("//tbody/tr/td/div/strong/a/@href").getall()[:20]

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


class CsrcNistGovSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=default_request_handler)
        self.router._handlers_by_label["fetch_articles"] = fetch_articles  # pyright: ignore [reportPrivateUsage]

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                Request.from_url(
                    "https://csrc.nist.gov/publications/search", label="fetch_articles"
                )
            ]
        )
