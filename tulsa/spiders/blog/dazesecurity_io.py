from datetime import datetime
from time import mktime
from typing import override
from urllib.parse import urljoin

from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog


class DazesecurityIo(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(["https://dazesecurity.io/blog"])

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        items = context.selector.xpath(
            '//div[@class="MuiGrid2-root MuiGrid2-direction-xs-row MuiGrid2-grid-xs-1 mui-g3uult"]'
        )
        for entry in items:
            title = entry.xpath(".//h5/text()").get()
            if not title:
                context.log.error(
                    f"{context.request.url} | Cannot find title HTML element"
                )
                continue
            url = entry.xpath(".//a/@href").get()
            if not url:
                context.log.error(
                    f"{context.request.url} | Cannot find url HTML element"
                )
                continue
            url = urljoin(context.request.loaded_url or context.request.url, url)
            thumbnail = entry.xpath(".//img/@src").get()
            published = entry.xpath(".//time/@datetime").get()

            item = Blog(url=url, title=title)
            if thumbnail:
                item.thumbnail = urljoin(
                    context.request.loaded_url or context.request.url, thumbnail
                )
            if published:
                published = parse_date(published)
                if published:
                    item.published = datetime.fromtimestamp(mktime(published))

            yield item
