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


class L3yxGithubIoSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(["https://l3yx.github.io"])

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        items = context.selector.xpath("//article")

        if len(items) == 0:
            context.log.error(f"{context.request.url} | Cannot find HTML element")
            return

        for entry in items:
            title = entry.xpath(".//h2/a/text()").get()
            if not title:
                context.log.error(f"{context.request.url} | Cannot find title element")
                return
            url = entry.xpath(".//h2/a/@href").get()
            if not url:
                context.log.error(f"{context.request.url} | Cannot find url element")
                return
            url = urljoin(context.request.loaded_url or context.request.url, url)
            published = entry.xpath(".//time/@datetime").get()
            description = entry.xpath("./div/p/text()").get()

            item = Blog(url=url, title=title)
            if description:
                item.description = BeautifulSoup(description, "lxml").text
            if published:
                published = parse_date(published)
                if published:
                    item.published = datetime.fromtimestamp(mktime(published))

            yield item
