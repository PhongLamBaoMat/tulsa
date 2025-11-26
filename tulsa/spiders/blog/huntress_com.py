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


class HuntressComSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)
        self.router._handlers_by_label["fetch_articles"] = self.fetch_articles  # pyright: ignore [reportPrivateUsage]

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                Request.from_url(url, label="fetch_articles")
                for url in [
                    "https://www.huntress.com/blog-categories/threat-analysis",
                    "https://www.huntress.com/blog-categories/response-to-incidents",
                ]
            ]
        )

    @staticmethod
    async def fetch_articles(context: ParselCrawlingContext):
        await context.add_requests(
            [
                Request.from_url(
                    urljoin(context.request.loaded_url or context.request.url, url)
                )
                for url in context.selector.xpath(
                    '//div[@role="listitem" and @class="collection-item resources-item "]/a/@href'
                ).getall()[:5]
            ]
        )

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        item = Blog.from_html_selector(context.selector)
        if not item:
            context.log.error(
                f"{context.request.url} | Cannot find url or title HTML element"
            )
            return
        published = context.selector.xpath(
            '//a[@class="breadcrumb-link breadcrumb-link-back"]/text()'
        ).get()
        if published:
            published = parse_date(published)
            if published:
                item.published = datetime.fromtimestamp(mktime(published))

        item.title = item.title.removesuffix(" | Huntress")
        yield item
