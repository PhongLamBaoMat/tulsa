import json
from typing import override

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
            f"{context.request.url} | Cannot find <script type='application/ld+json'> HTML element"
        )
        return
    for entry in json.loads(data).get("hasPart", []):
        item = Blog.from_json_schema(entry)
        if not item:
            continue
        item.category = Category.Blockchain

        yield item


class CoinspectComSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(["https://www.coinspect.com/blog"])
