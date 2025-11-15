from datetime import datetime
from time import mktime
from typing import override
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog


class DreyandRsSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(["https://dreyand.rs"])

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        items = context.selector.xpath('//ul[@class="posts"]/li')

        if len(items) == 0:
            context.log.error(f"{context.request.url} | Cannot find HTML element")
            return

        for entry in items:
            if entry.attrib != {}:
                continue

            title = entry.xpath(".//h2/text()").get()
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
            published = parse_date(
                "".join(
                    map(
                        lambda x: x.get(),
                        entry.xpath('.//div[@class="post-date"]/text()'),
                    )
                ).strip()
            )

            description = entry.xpath('.//div[@class="post"]/p').get()

            item = Blog(url=url, title=title)
            if description:
                item.description = BeautifulSoup(description, "lxml").text
            if published:
                item.published = datetime.fromtimestamp(mktime(published))

            yield item
