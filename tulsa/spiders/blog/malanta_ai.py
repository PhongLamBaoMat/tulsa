from datetime import datetime
from time import mktime
from typing import override
from urllib.parse import urljoin

from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog


class MalantaAiSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(["https://www.malanta.ai/blog"])

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        # context.log.info(f"{await context.http_response.read()}")
        items = context.selector.xpath(
            '//div[@role="listitem" and @class="resources_grid-item w-dyn-item"]'
        )

        if len(items) == 0:
            context.log.error(f"{context.request.url} | Cannot find HTML element")
            return

        first = True
        for entry in items:
            category = entry.xpath('.//div[@fs-list-field="category"]/text()').get()
            # The site contains many posts but some of them are written by malanta.ai
            if not category or category != "blog":
                # Extract the first post because it doesn't have category
                if not first:
                    continue
                first = False
            url = entry.xpath(".//a/@href").get()
            if not url:
                context.log.error(
                    f"{context.request.url} | Cannot find url HTML element"
                )
                return
            url = urljoin(context.request.loaded_url or context.request.url, url)
            title = entry.xpath(".//h3/text()").get()
            if not title:
                context.log.error(
                    f"{context.request.url} | Cannot find title HTML element"
                )
                return
            thumbnail = entry.xpath(".//img/@src").get()
            # The first post has 2 elements so we pick the last one
            published = entry.xpath(
                './/div[@class="text-size-caption"]/text()'
            ).getall()[-1]

            item = Blog(url=url, title=title)
            if thumbnail:
                item.thumbnail = thumbnail
            if published:
                published = parse_date(published)
                if published:
                    item.published = datetime.fromtimestamp(mktime(published))

            yield item
