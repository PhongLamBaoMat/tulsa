from datetime import datetime
from time import mktime
from typing import override
from urllib.parse import urljoin

from crawlee import Request
from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import HtmlSpider
from tulsa.helpers import parse_date
from tulsa.models import Blog, Category


async def default_request_handler(context: ParselCrawlingContext):
    item = Blog.from_html_selector(context.selector)
    if not item:
        context.log.error(
            f"{context.request.url}| Cannot find url or title HTML element"
        )
        return
    if not item.thumbnail:
        thumbnail = context.selector.xpath('//img[@class="blogp-image"]/@src').get()
        if thumbnail:
            item.thumbnail = urljoin(
                context.request.loaded_url or context.request.url, thumbnail
            )
    published = context.selector.xpath(
        '//div[@class="blogp-headingdate"]/div[@class="text-size-large"]/text()'
    ).get()
    item.title = item.title.replace(" - ChainSecurity", "")
    item.category = Category.Blockchain
    if published:
        published = parse_date(published)
        if published:
            item.published = datetime.fromtimestamp(mktime(published))

    yield item


async def fetch_articles(context: ParselCrawlingContext):
    await context.add_requests(
        [
            Request.from_url(
                urljoin(context.request.loaded_url or context.request.url, url)
            )
            for url in context.selector.xpath(
                '//div[@role="listitem"]/a/@href'
            ).getall()
        ]
    )


class ChainsecurityComSpider(HtmlSpider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=default_request_handler)
        self.router._handlers_by_label["fetch_articles"] = fetch_articles  # pyright: ignore [reportPrivateUsage]

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                Request.from_url(
                    "https://www.chainsecurity.com/blog", label="fetch_articles"
                )
            ]
        )
