import re
from datetime import datetime
from time import mktime
from typing import override

from crawlee import Request
from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog


async def bypass_redirect(context: ParselCrawlingContext):
    body = (await context.http_response.read()).decode()
    match = re.search(r"document\.cookie=\"([=\w]+)\"", body, re.M)
    if match:
        cookie = match.group(1)
        await context.add_requests(
            [
                Request.from_url(
                    context.request.url,
                    headers={"Cookie": cookie, "Referer": context.request.url},
                    use_extended_unique_key=True,
                )
            ]
        )
    else:
        context.log.error(f"{context.request.url} | Cannot find cookie")


class ViettelSecurityResearchSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)
        self.router._handlers_by_label["bypass_redirect"] = bypass_redirect  # pyright: ignore [reportPrivateUsage]

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                Request.from_url(
                    "https://viettelsecurity.com/vi/nghien-cuu-chuyen-sau/",
                    label="bypass_redirect",
                )
            ]
        )

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        items = context.selector.xpath(
            '//div[@class="theme-card rounded-16 border border-solid flex flex-col items-start overflow-hidden"]'
        )
        if len(items) == 0:
            context.log.error(f"{context.request.url} | Cannot find HTML element")
            return

        for entry in items:
            title = entry.xpath(".//h3/a/text()").get()
            if not title:
                context.log.error(
                    f"{context.request.url} | Cannot find title HTML element"
                )
                continue
            url = entry.xpath(".//h3/a/@href").get()
            if not url:
                context.log.error(
                    f"{context.request.url} | Cannot find url HTML element"
                )
                continue
            description = entry.xpath(
                './/p[@class="mb-0 text-14 text-body-secondary text-truncate-3 "]/text()'
            ).get()
            published = entry.xpath(".//time/@datetime").get()

            item = Blog(url=url, title=title)
            if description:
                item.description = description
            if published:
                day, month, year = published.split("/")
                published = parse_date(f"{year}-{month}-{day}")
                if published:
                    item.published = datetime.fromtimestamp(mktime(published))

            yield item


class ViettelSecurityReportSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)
        self.router._handlers_by_label["bypass_redirect"] = bypass_redirect  # pyright: ignore [reportPrivateUsage]

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                Request.from_url(
                    "https://viettelsecurity.com/vi/resource-report/",
                    label="bypass_redirect",
                )
            ]
        )

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        items = context.selector.xpath(
            '//div[@class="resource-card-item theme-card rounded-16 border border-solid flex flex-col items-start overflow-hidden h-full"]'
        )
        if len(items) == 0:
            context.log.error(f"{context.request.url} | Cannot find HTML element")
            return

        for entry in items:
            title = entry.xpath(".//h3/a/text()").get()
            if not title:
                context.log.error(
                    f"{context.request.url} | Cannot find title HTML element"
                )
                continue
            url = entry.xpath(".//h3/a/@href").get()
            if not url:
                context.log.error(
                    f"{context.request.url} | Cannot find url HTML element"
                )
                continue
            thumbnail = entry.xpath(".//img/@src").get()
            published = entry.xpath(".//time/@datetime").get()

            item = Blog(url=url, title=title)
            if thumbnail:
                item.thumbnail = thumbnail
            if published:
                day, month, year = published.split("/")
                published = parse_date(f"{year}-{month}-{day}")
                if published:
                    item.published = datetime.fromtimestamp(mktime(published))

            yield item
