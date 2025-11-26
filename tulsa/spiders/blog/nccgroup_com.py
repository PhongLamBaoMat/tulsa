from datetime import datetime
from time import mktime
from typing import override
from urllib.parse import urljoin

from crawlee import Request
from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog


class NccgroupComSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)
        self.router._handlers_by_label["fetch_articles"] = self.fetch_articles  # pyright: ignore [reportPrivateUsage]

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                Request.from_url(
                    "https://www.nccgroup.com/us/research-blog",
                    label="fetch_articles",
                )
            ]
        )

    @staticmethod
    async def fetch_articles(context: ParselCrawlingContext):
        await context.add_requests(
            [
                Request.from_url(
                    urljoin(context.request.loaded_url or context.request.url, url)
                )
                for url in context.selector.xpath("//h3/a/@href").getall()
            ]
        )

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        item = Blog.from_html_selector(context.selector)
        if not item:
            context.log.error(
                f"{context.request.url} | Cannot find title or url HTML element"
            )
            return
        published = context.selector.xpath('//p[@class="c-banner__date"]/text()').get()
        if published:
            published = parse_date(published)
            if published:
                item.published = datetime.fromtimestamp(mktime(published))
        yield item
