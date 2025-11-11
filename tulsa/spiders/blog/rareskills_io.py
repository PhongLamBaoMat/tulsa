from collections.abc import AsyncIterator
from datetime import datetime
from time import mktime
from typing import override

from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import HtmlSpider
from tulsa.helpers import parse_date
from tulsa.models import Blog, Category


async def default_request_handler(
    context: ParselCrawlingContext,
) -> AsyncIterator[Blog]:
    items = context.selector.xpath('//div[@class="brxe-ykotbt brxe-div blog-card"]')
    if len(items):
        context.log.error(f"{context.request.url} | Cannot find the HTML element")
        return
    for entry in items:
        url = entry.xpath("./a/@href").get()
        if not url:
            context.log.error(f"{context.request.url} | Cannot find url HTML element")
            return
        title = entry.xpath("./h3/text()").get()
        if not title:
            context.log.error(f"{context.request.url} | Cannot find title HTML element")
            return
        description = entry.xpath(
            './/div[@class="brxe-cxwyxl brxe-post-excerpt blog-card-excerpt"]/p/text()'
        ).get()
        thumbnail = entry.xpath(".//img/@src").get()
        published = entry.xpath(
            './/span[@class="brxe-dcuqts brxe-text-basic blog-card-meta"]/text()'
        ).get()

        item = Blog(url=url, title=title, category=Category.Blockchain)
        if description:
            item.description = description.strip()
        if thumbnail:
            item.thumbnail = thumbnail
        if published:
            published = parse_date(published)
            if published:
                item.published = datetime.fromtimestamp(mktime(published))

        yield item


class RareskillIoSpider(HtmlSpider):
    def __init__(self):
        super().__init__(default_request_handler=default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(["https://rareskills.io/blog"])
