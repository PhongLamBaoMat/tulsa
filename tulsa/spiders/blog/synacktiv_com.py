from datetime import datetime
from time import mktime
from typing import override
from urllib.parse import urljoin

from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog


class SynacktiveComSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(["https://www.synacktiv.com/en/publications"])

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        items = context.selector.xpath("//article")

        if len(items) == 0:
            context.log.error(f"{context.request.url} | Cannot find HTML element")
            return

        for entry in items:
            title = entry.xpath('.//span[@property="schema:name"]/text()').get()
            if not title:
                context.log.error(
                    f"{context.request.url} | Cannot find title HTML element"
                )
                continue
            url = entry.xpath(".//h2/a/@href").get()
            if not url:
                context.log.error(
                    f"{context.request.url} | Cannot file url HTML element"
                )
                continue
            url = urljoin(context.request.loaded_url or context.request.url, url)
            published = entry.xpath("./div/span/i/text()").get()
            description = "".join(
                entry.xpath('.//div[@class="content"]/text()').getall()
            )
            thumbnail = entry.xpath('.//img[@class="img-responsive"]/@src').get()

            item = Blog(url=url, title=title)
            if description:
                item.description = description
            if thumbnail:
                item.thumbnail = urljoin(
                    context.request.loaded_url or context.request.url, thumbnail
                )
            if published:
                published = parse_date(published.replace("/", "-"))
                if published:
                    item.published = datetime.fromtimestamp(mktime(published))

            yield item
