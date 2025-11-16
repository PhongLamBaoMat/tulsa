from datetime import datetime
from time import mktime
from typing import override
from urllib.parse import urljoin

from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog


class OwnSecuritySpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(["https://www.own.security/en/ressources/analysis"])

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        items = context.selector.xpath(
            '//div[@class="actu_list is-publications w-dyn-items"]/div[@role="listitem"]'
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
                return
            url = entry.xpath(".//a/@href").get()
            if not url:
                context.log.error(
                    f"{context.request.url} | Cannot find url HTML element"
                )
                return
            url = urljoin(context.request.loaded_url or context.request.url, url)
            published = entry.xpath(".//div[@data-date]/text()").get()

            description = entry.xpath(
                './/p[@class="text-color-secondary"]/text()'
            ).get()
            thumbnail = entry.xpath(".//img/@src").get()

            item = Blog(url=url, title=title)
            if description:
                item.description = description
            if thumbnail:
                item.thumbnail = thumbnail
            if published:
                day, month, year = published.split("/")
                published = parse_date(f"{year}-{month}-{day}")
                if published:
                    item.published = datetime.fromtimestamp(mktime(published))

            yield item
