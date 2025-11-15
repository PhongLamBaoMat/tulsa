from datetime import datetime
from time import mktime
from typing import override
from urllib.parse import urljoin

from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog


class CorelabsCoresecurityComSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(["https://www.coresecurity.com/core-labs/articles"])

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        items = context.selector.xpath('//div[@class="pb-4 views-row"]')

        if len(items) == 0:
            context.log.error(f"{context.request.url} | Cannot find HTML element")
            return

        for entry in items:
            title = entry.xpath(".//h3/a/text()").get()
            if not title:
                context.log.error(
                    f"{context.request.url} | Cannot find url HTML element"
                )
                continue
            url = entry.xpath(".//h3/a/@href").get()
            if not url:
                context.log.error(
                    f"{context.request.url} | Cannot find title HTML element"
                )
                continue
            url = urljoin(context.request.loaded_url or context.request.url, url)
            description = entry.xpath('.//div[@class="field-content"]/text()').get()
            published = entry.xpath('.//time[@class="datetime"]/@datetime').get()

            item = Blog(url=url, title=title)
            if description:
                item.description = description
            if published:
                published = parse_date(published)
                if published:
                    item.published = datetime.fromtimestamp(mktime(published))

            yield item
