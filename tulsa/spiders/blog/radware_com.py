from datetime import datetime
from time import mktime
from typing import override
from urllib.parse import urljoin

from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog


class RadwareComSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(["https://www.radware.com/blog/threat-intelligence/"])

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        items = context.selector.xpath("//article")

        if len(items) == 0:
            context.log.error(f"{context.request.url} | Cannot find url HTML element")
            return

        for entry in items:
            title = entry.xpath('.//span[@class="heading-4 m-b-1"]/text()').get()
            if not title:
                context.log.error(
                    f"{context.request.url} | Cannot find title HTML element"
                )
                continue
            url = entry.xpath("./a/@href").get()
            if not url:
                context.log.error(
                    f"{context.request.url} | Cannot find url HTML element"
                )
                continue
            url = urljoin(context.request.loaded_url or context.request.url, url)
            description = entry.xpath(
                './/span[@class="feature-card__text"]/text()'
            ).get()
            thumbnail = entry.xpath(".//img/@src").get()
            published = entry.xpath('.//span[@class="info m-t-1"]').get()

            item = Blog(url=url, title=title)
            if description:
                item.description = description
            if thumbnail:
                item.thumbnail = urljoin(
                    context.request.loaded_url or context.request.url, thumbnail
                )
            if published:
                published = parse_date(published.split("</b>")[-1])
                if published:
                    item.published = datetime.fromtimestamp(mktime(published))

            yield item
