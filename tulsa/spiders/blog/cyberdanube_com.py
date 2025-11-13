from typing import override

from crawlee import Request
from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.models import Blog


async def default_request_handler(context: ParselCrawlingContext):
    item = Blog.from_html_selector(context.selector)
    if not item:
        context.log.error(
            f"{context.request.url} | Cannot find url or title HTML elelemt"
        )
        return

    item.title = item.title.replace(" | CyberDanube", "")

    yield item


async def fetch_articles(context: ParselCrawlingContext):
    items = context.selector.xpath("//article/div/div/a/@href").getall()
    if len(items) == 0:
        context.log.error(f"{context.request.url} | Cannot find the HTML element")
        return

    await context.add_requests([url for url in items])


class CyberdanubeComSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=default_request_handler)
        self.router._handlers_by_label["fetch_articles"] = fetch_articles  # pyright: ignore [reportPrivateUsage]

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                Request.from_url(
                    "https://cyberdanube.com/security-research/", label="fetch_articles"
                )
            ]
        )
