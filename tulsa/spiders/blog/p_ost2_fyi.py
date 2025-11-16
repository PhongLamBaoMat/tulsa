from datetime import datetime
from time import mktime
from typing import override
from urllib.parse import urljoin

from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog


class OpenSecurityTraining2Spider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(["https://p.ost2.fyi"])

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        items = context.selector.xpath("//article")

        if len(items) == 0:
            context.log.error(f"{context.request.url} | Cannot find HTML element")
            return

        for entry in items:
            title = entry.xpath('.//span[@class="course-title"]/text()').get()
            if not title:
                context.log.error(f"{context.request.url} | Cannot find title HTML")
                continue
            # This isn't an article
            if title == "YOUR CLASS HERE!":
                continue
            url = entry.xpath("./a/@href").get()
            if not url:
                context.log.error(f"{context.request.url} | Cannot find url HTML")
                continue
            url = urljoin(context.request.loaded_url or context.request.url, url)
            published = entry.xpath(
                './/div[@class="course-date localized_datetime"]/@data-datetime'
            ).get()
            thumbnail = entry.xpath('.//div[@class="cover-image"]/img/@src').get()

            item = Blog(url=url, title=title)
            item.author = "OpenSecurityTraining2"
            if thumbnail:
                item.thumbnail = urljoin(
                    context.request.loaded_url or context.request.url, thumbnail
                )
            if published:
                published = parse_date(published)
                if published:
                    item.published = datetime.fromtimestamp(mktime(published))

            yield item
