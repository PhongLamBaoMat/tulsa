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


class KarmainsecurityCom(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(["https://karmainsecurity.com/blog"])

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        items = context.selector.xpath("//main/div/div/a")

        if len(items) == 0:
            context.log.error(f"{context.request.url} | Cannot find HTML element")
            return

        for entry in items:
            title = entry.xpath('.//span[@class="postTitle"]/text()').get()
            if not title:
                context.log.error(
                    f"{context.request.url} | Cannot find title HTML element"
                )
                continue
            url = entry.xpath("./@href").get()
            if not url:
                context.log.error(
                    f"{context.request.url} | Cannot find url HTML element"
                )
                continue
            url = urljoin(context.request.loaded_url or context.request.url, url)
            published = entry.xpath('.//time[@class="postDate"]/@datetime').get()
            description = entry.xpath('.//div[@class="postExcerpt"]').get()

            item = Blog(url=url, title=title)
            context.html_to_text
            if description:
                item.description = BeautifulSoup(description, "lxml").text
            if published:
                published = parse_date(published)
                if published:
                    item.published = datetime.fromtimestamp(mktime(published))

            yield item
