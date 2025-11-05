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
    for entry in context.selector.xpath('//div[@class="blog__item__inner"]'):
        title = entry.xpath(".//h2/a/text()").get()
        if not title:
            context.log.error(f"{context.request.url} | Cannot find title HTML element")
            return
        url = entry.xpath(".//h2/a/@href").get()
        if not url:
            context.log.error(f"{context.request.url} | Cannot find url HTML element")
            return
        url = urljoin(context.request.loaded_url or context.request.url, url)
        description = entry.xpath('.//div[@class="blog__item__excerpt"]').get()
        thumbnail = entry.xpath(".//img/@data-src").get()
        published = entry.xpath(".//time/@datetime").get()

        item = Blog(url=url, title=title)
        if description:
            item.description = BeautifulSoup(description, "lxml").text.strip()
        if thumbnail:
            item.thumbnail = thumbnail
        if published:
            published = parse_date(published)
            if published:
                item.published = datetime.fromtimestamp(mktime(published))

        context.log.info(item)
        yield item


class AfineComSpider(HtmlSpider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(["https://afine.com/blog/"])
