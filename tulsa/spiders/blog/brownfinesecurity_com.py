from datetime import datetime
from time import mktime
from typing import override
from urllib.parse import urljoin

from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import HtmlSpider
from tulsa.helpers import parse_date
from tulsa.models import Blog


async def default_request_handler(context: ParselCrawlingContext):
    items = context.selector.xpath(
        '//div[@class="grid grid-cols-1 md:grid-cols-2 md:gap-x-16 lg:gap-x-32 gap-y-20 md:gap-y-32 mb-32"]'
    ).xpath("./div")
    if len(items) == 0:
        context.log.error(f"{context.request.url} | Cannot find the HTML element")
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
        description = entry.xpath(
            './/p[@class="text-lg leading-relaxed mb-4"]/text()'
        ).get()
        thumbnail = entry.xpath(".//img/@src").get()
        published = entry.xpath(".//time/@datetime").get()

        item = Blog(url=url, title=title)
        if description:
            item.description = description.strip()
        if thumbnail:
            item.thumbnail = urljoin(
                context.request.loaded_url or context.request.url, thumbnail
            )
        if published:
            published = parse_date(published)
            if published:
                item.published = datetime.fromtimestamp(mktime(published))

        yield item


class BrownfinesecurityCom(HtmlSpider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(["https://brownfinesecurity.com/blog"])
