from datetime import datetime
from time import mktime
from typing import override

from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog


class QualysComSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            ["https://www.qualys.com/research/security-advisories/"]
        )

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        items = context.selector.xpath(
            '//ul[@class="list-none p-0 flex flex-col gap-15"]/li'
        )

        if len(items) == 0:
            context.log.error(f"{context.request.url} | Cannot find HTML element")
            return

        for entry in items:
            title = entry.xpath(".//h4/text()").get()
            if not title:
                context.log.error(
                    f"{context.request.url} | Cannot find title HTML element"
                )
                continue
            url = entry.xpath(".//a/@href").get()
            if not url:
                context.log.error(
                    f"{context.request.url} | Cannot find url HTML element"
                )
                continue
            published = entry.xpath("./div/text()").get()

            item = Blog(url=url, title=title)
            if published:
                published = parse_date(published)
                if published:
                    item.published = datetime.fromtimestamp(mktime(published))

            yield item
