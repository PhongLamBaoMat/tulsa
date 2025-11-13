import json
from typing import override

from crawlee import Request
from crawlee.crawlers import (
    ParselCrawlingContext,
)
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.models import Blog


async def default_request_handler(context: ParselCrawlingContext):
    data = context.selector.xpath('//script[@type="application/ld+json"]/text()').get()
    if not data:
        context.log.error(
            f'{context.request.url} | Cannot find <script type="application/ld+json"> HTML element'
        )
        return
    item = None
    for graph in json.loads(data)["@graph"]:
        if graph["@type"] == "WebSite":
            item = Blog.from_json_schema(graph)
            break
    if not item:
        context.log.error(
            f"{context.request.url} | Cannot find title or url HTML element"
        )
        return

    yield item


async def fetch_articles(context: ParselCrawlingContext):
    items = json.loads(await context.http_response.read())["data"]

    await context.add_requests([entry["url"] for entry in items][:20])


class BinarydefenseComSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=default_request_handler)
        self.router._handlers_by_label["fetch_articles"] = fetch_articles  # pyright: ignore [reportPrivateUsage]

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                Request.from_url(
                    "https://binarydefense.com/arclabs.json", label="fetch_articles"
                )
            ]
        )
