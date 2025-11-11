from datetime import datetime
from time import mktime
from typing import override
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import HtmlSpider
from tulsa.helpers import parse_date
from tulsa.models import Blog


async def default_request_handler(context: ParselCrawlingContext):
    items = context.selector.xpath('//div[@class="row category_article flex-lg-row"]')

    if len(items) == 0:
        raise ValueError(f"Cannot find HTLM elements: {context.request.url}")

    for entry in items:
        title = entry.xpath(".//h3/a/text()").get()
        if not title:
            context.log.error("Cannot find title HTML element")
            return
        url = entry.xpath(".//h3/a/@href").get()
        if not url:
            context.log.error("Cannot find url HTML element")
            return
        url = urljoin(context.request.loaded_url or context.request.url, url)
        published = entry.xpath('.//div[@class="publish_info"]/p/text()').get()
        description = entry.xpath('.//div[@class="excerpt"]').get()
        thumbnail = entry.xpath(".//img/@src").get()

        item = Blog(url=url, title=title.strip())
        if description:
            item.description = BeautifulSoup(description, "lxml").text.strip()
        if published:
            published = parse_date(published)
            if published:
                item.published = datetime.fromtimestamp(mktime(published))
        if thumbnail:
            item.thumbnail = urljoin(
                context.request.loaded_url or context.request.url, thumbnail
            )

        yield item


class CrowdstrikeComSpider(HtmlSpider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                "https://www.crowdstrike.com/en-us/blog/category.engineering-and-technology/",
                "https://www.crowdstrike.com/en-us/blog/category.counter-adversary-operations/",
            ]
        )
