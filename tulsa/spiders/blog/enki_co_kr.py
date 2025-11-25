from datetime import datetime
from time import mktime
from typing import override
from urllib.parse import urljoin

from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog


class EnkiCoKrSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(["https://www.enki.co.kr/en/media-center/blog"])

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        items = context.selector.xpath('.//div[@class="framer-t23jlf-container"]')
        if len(items) == 0:
            context.log.error(f"{context.request.url} | Cannot find HTML element")
            return

        for entry in items:
            title = entry.xpath(".//h3/text()").get()
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
            category = entry.xpath('.//div[@class="framer-fqa8bo"]/p/text()').get()
            if not category:
                context.log.error(
                    f"{context.request.url} | Cannot find category HTML element"
                )
                continue
            if (
                category != "Threat Intelligence"
                and category != "Vulnerability research"
            ):
                continue
            url = urljoin(context.request.loaded_url or context.request.url, url)
            thumbnail = entry.xpath(".//img/@src").get()
            published = entry.xpath('.//div[@class="framer-1vztn4h"]/p/text()').get()

            item = Blog(url=url, title=title)
            if thumbnail:
                item.thumbnail = thumbnail
            if published:
                published = parse_date(published)
                if published:
                    item.published = datetime.fromtimestamp(mktime(published))

            yield item
