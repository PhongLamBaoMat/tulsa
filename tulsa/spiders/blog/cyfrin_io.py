from datetime import datetime
from time import mktime
from typing import override
from urllib.parse import urljoin

from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog, Category

month_dict = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}


class CyfrinIoSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(["https://www.cyfrin.io/blog"])

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        items = context.selector.xpath(
            '//div[@role="listitem" and @class="blog-2-0-collection-item w-dyn-item"]'
        )

        if len(items) == 0:
            context.log.error(f"{context.request.url} | Cannot find HTML element")
            return

        for entry in items:
            title = entry.xpath(".//h2/text()").get()
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
            url = urljoin(context.request.loaded_url or context.request.url, url)
            # We skip News category
            if (
                entry.xpath('.//div[@class="blog-badges"]/div/div/text()').get() or ""
            ) == "News":
                continue
            published = entry.xpath('.//div[@class="blog-2-0-publish-date"]/div/text()')
            description = (
                entry.xpath(
                    './/div[@class="text-md-regular blog-2-0-excerpt"]/text()'
                ).get()
                or entry.xpath('.//div[@class="text-md-regular"]/text()').get()
            )

            item = Blog(url=url, title=title.strip())
            if description:
                item.description = description
            if len(published) == 3:
                published = parse_date(
                    f"{published[2].get()}-{month_dict[published[1].get()]}-{published[0].get()}"
                )
                if published:
                    item.published = datetime.fromtimestamp(mktime(published))
            item.category = Category.Blockchain

            yield item
