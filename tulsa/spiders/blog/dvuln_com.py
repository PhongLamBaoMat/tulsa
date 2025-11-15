from datetime import datetime
from time import mktime
from typing import override
from urllib.parse import urljoin

from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog


class DvulnComSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(["https://dvuln.com/blog"])

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        items = context.selector.xpath('//a[@class="framer-kpqeu framer-oltf"]')

        if len(items) == 0:
            context.log.error(f"{context.request.url} | Cannot find HTML element")
            return

        for entry in items:
            title = entry.xpath(
                './/p[@class="framer-text framer-styles-preset-po9ocu"]/text()'
            ).get()
            if not title:
                context.log.error(f"{context.request.url} | Cannot find title element")
                continue
            url = entry.xpath("@href").get()
            if not url:
                context.log.error(f"{context.request.url} | Cannot find url element")
                continue
            url = urljoin(context.request.loaded_url or context.request.url, url)
            published = entry.xpath(
                './/p[@class="framer-text framer-styles-preset-1t0jlse"]/text()'
            )[2].get()
            thumbnail = entry.xpath(".//img/@src")[1].get()

            item = Blog(url=url, title=title)
            if thumbnail:
                item.thumbnail = thumbnail
            if published:
                published = parse_date(published)
                if published:
                    item.published = datetime.fromtimestamp(mktime(published))

            yield item
