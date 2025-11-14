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


async def default_request_handler(context: ParselCrawlingContext):
    items = context.selector.xpath('//div[@class=" item-card enisa-card"]')
    if len(items) == 0:
        context.log.error(f"{context.request.url} | Cannot find HTML element")
        return

    for entry in items:
        title = entry.xpath(".//h3/a/text()").get()
        if not title:
            context.log.error(f"{context.request.url} | Cannot find title HTML element")
            continue
        url = entry.xpath(".//h3/a/@href").get()
        if not url:
            context.log.error(f"{context.request.url} | Cannot find url HTML element")
            continue
        url = urljoin(context.request.loaded_url or context.request.url, url)
        description = entry.xpath('.//div[@class="content"]/p/text()').get()
        published = entry.xpath(".//time/@datetime").get()

        item = Blog(url=url.strip(), title=title.strip())
        if description:
            item.description = description.strip()
        if published:
            published = parse_date(published)
            if published:
                item.published = datetime.fromtimestamp(mktime(published))

        yield item

    items = context.selector.xpath('//div[@class="publications-item"]')
    if len(items) == 0:
        context.log.error(f"{context.request.url} | Cannot find HTML element")
        return
    for entry in items:
        title = entry.xpath(".//h3/a/text()").get()
        if not title:
            context.log.error(f"{context.request.url} | Cannot find title HTML element")
            return
        url = entry.xpath(".//h3/a/@href").get()
        if not url:
            context.log.error(f"{context.request.url} | Cannot find url HTML element")
            return
        url = urljoin(context.request.loaded_url or context.request.url, url)
        description = entry.xpath('.//div[@class="content"]/p').get()
        thumbnail = entry.xpath(".//img/@src").get()
        published = entry.xpath(".//time/@datetime").get()

        item = Blog(url=url.strip(), title=title.strip())
        if description:
            item.description = BeautifulSoup(description, "lxml").text.strip()
        if thumbnail:
            item.thumbnail = urljoin(
                context.request.loaded_url or context.request.url, thumbnail
            )
        if published:
            published = parse_date(published)
            if published:
                item.published = datetime.fromtimestamp(mktime(published))

        yield item


class EnisaEuropaEuSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(["https://www.enisa.europa.eu/publications"])
