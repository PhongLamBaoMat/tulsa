from collections.abc import AsyncIterator
from datetime import datetime
from time import mktime
from typing import override

from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import HtmlSpider
from tulsa.helpers import is_valid_url, parse_date
from tulsa.models import Blog


async def default_request_handler(
    context: ParselCrawlingContext,
) -> AsyncIterator[Blog]:
    for entry in context.selector.xpath('//div[@class="post-card"]'):
        title = entry.xpath(".//h3/a/text()").get()
        if not title:
            context.log.error(f"{context.request.url} | Cannot find title HTML element")
            return
        url = entry.xpath(".//a/@href").get()
        if not url:
            context.log.error(f"{context.request.url} | Cannot find url HTML element")
            return
        description = entry.xpath('.//div[@class="content-wrap"]/p/text()').get()
        thumbnail = None
        for img in entry.xpath(".//img/@src").getall():
            if is_valid_url(img):
                thumbnail = img
                break
        published = None
        for li in entry.xpath('.//ul[@class="details"]/li/text()').getall():
            published = parse_date(li)
            if published:
                break

        item = Blog(url=url, title=title)
        if description:
            item.description = description.strip()
        if thumbnail:
            item.thumbnail = thumbnail
        if published:
            item.published = datetime.fromtimestamp(mktime(published))

        yield item


class SemperisComSpider(HtmlSpider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                "https://www.semperis.com/category/identity-attack-catalog",
                "https://www.semperis.com/category/identity-threat-detection-and-response/",
                "https://www.semperis.com/category/threat-research/",
            ]
        )
