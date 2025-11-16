import re
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

date_re = re.compile(r"(\d{1,2}) (\w{3}) (\d{4})")

month_dict = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}


class NccgroupComSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(["https://www.nccgroup.com/us/research-blog/"])

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        items = context.selector.xpath('//div[@class="c-lb__content"]')

        if len(items) == 0:
            context.log.error(f"{context.request.url} | Cannot find HTML element")
            return

        for entry in items:
            title = entry.xpath(".//h3/a/text()").get()
            if not title:
                context.log.error(
                    f"{context.request.url} | Cannot find title HTML element"
                )
                return
            url = entry.xpath(".//h3/a/@href").get()
            if not url:
                context.log.error(
                    f"{context.request.url} | Cannot find title HTML element"
                )
                return
            url = urljoin(context.request.loaded_url or context.request.url, url)
            published = entry.xpath(
                './/div[@class="blog-date with-icon"]/p/text()'
            ).get()

            description = entry.xpath('.//span[@class="c-lb__text"]/p/text()').get()

            item = Blog(url=url, title=title)
            if description:
                item.description = BeautifulSoup(description, "lxml").text
            if published:
                m = date_re.match(published)
                if not m:
                    raise ValueError(
                        f"Failed to parsed '{published}': {context.request.url}"
                    )
                day = m.group(1)
                month = month_dict[m.group(2)]
                year = m.group(3)
                published = parse_date(f"{year}-{month}-{day}")
                if published:
                    item.published = datetime.fromtimestamp(mktime(published))

            yield item
