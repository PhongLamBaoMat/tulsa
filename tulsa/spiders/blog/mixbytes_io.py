from datetime import datetime
from time import mktime
from typing import cast, override
from urllib.parse import urljoin

from crawlee import Request
from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog, Category


class MixbytesIoSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)
        self.router._handlers_by_label["fetch_articles"] = self.fetch_articles  # pyright: ignore [reportPrivateUsage]

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [Request.from_url("https://mixbytes.io/blog", label="fetch_articles")]
        )

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        item = Blog.from_html_selector(context.selector)
        if not item:
            context.log.error(
                f"{context.request.url} | Cannot find url or title HTML element"
            )
            return
        date = cast(str | None, context.request.user_data.get("date"))  # pyright: ignore [reportUnknownMemberType]
        if date:
            published = parse_date(date)
            if published:
                item.published = datetime.fromtimestamp(mktime(published))
        item.category = Category.Blockchain

        yield item

    @staticmethod
    async def fetch_articles(context: ParselCrawlingContext):
        items = context.selector.xpath('//div[@class="t404"]/div[@class="t-container"]')

        if len(items) == 0:
            context.log.error(f"{context.request.url} | Cannot find HTML element")
            return

        count = 0
        requests: list[Request] = []
        for item in items:
            count += 1
            if count > 10:
                break
            url = item.xpath(".//a/@href").get()
            if not url:
                continue
            date = item.xpath('.//span[@class="t404__date"]/text()').get()
            requests.append(
                Request.from_url(
                    urljoin(context.request.loaded_url or context.request.url, url),
                    user_data={"date": date},
                )
            )

        await context.add_requests(requests)
