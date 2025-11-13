import json
from typing import override

from crawlee import Request
from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.models import Blog, Category


async def default_request_handler(context: ParselCrawlingContext):
    data = context.selector.xpath(
        '//head/script[@type="application/ld+json"]/text()'
    ).get()
    if not data:
        context.log.error(
            f'{context.request.url} | Cannot find <script type="application/ld+json"> HTML element'
        )
        return

    item = Blog.from_json_schema(json.loads(data))
    if not item:
        context.log.error(
            f"{context.request.url} | Cannot find url or title in the json data"
        )
        return
    item.category = Category.BugBounty

    if item.description:
        item.description = item.description.lstrip(item.title)

    yield item


async def fetch_articles(context: ParselCrawlingContext):
    await context.add_requests(
        [
            Request.from_url(url)
            for url in context.selector.xpath("//item/guid/text()").getall()
        ]
    )


class MediumComTagSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=default_request_handler)
        self.router._handlers_by_label["fetch_articles"] = fetch_articles  # pyright: ignore [reportPrivateUsage]

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                Request.from_url(url, label="fetch_articles")
                for url in [
                    "https://medium.com/feed/tag/bug-bounty",
                    "https://medium.com/feed/tag/bug-bounty-tips",
                ]
            ]
        )
