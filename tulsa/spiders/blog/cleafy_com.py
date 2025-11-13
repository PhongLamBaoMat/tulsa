from datetime import datetime
from time import mktime
from typing import cast, override
from urllib.parse import urljoin

from crawlee import Request
from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog


async def default_request_handler(context: ParselCrawlingContext):
    item = Blog.from_html_selector(context.selector)
    if not item:
        context.log.error(
            f"{context.request.url} | Cannot find url or title HTML element"
        )
        return
    published = cast(str | None, context.request.user_data.get("published"))  # pyright: ignore [reportUnknownMemberType]
    if published:
        published = parse_date(published)
        if published:
            item.published = datetime.fromtimestamp(mktime(published))

    yield item


async def fetch_articles(context: ParselCrawlingContext):
    requests: list[Request] = []
    for entry in context.selector.xpath(
        '//div[@role="list"]/div[@role="listitem" and @class="card-newsroom lab w-dyn-item"]'
    ):
        url = entry.xpath("./a/@href").get()
        if not url:
            context.log.error(f"{context.request.url} | Cannot find url HTML element")
            break
        url = urljoin(context.request.loaded_url or context.request.url, url)
        published = entry.xpath('./p[@class="mono"]/text()').get()
        requests.append(Request.from_url(url, user_data={"published": published}))

    await context.add_requests(requests)


class CleafyComSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=default_request_handler)
        self.router._handlers_by_label["fetch_articles"] = fetch_articles  # pyright: ignore [reportPrivateUsage]

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [Request.from_url("https://www.cleafy.com/labs", label="fetch_articles")]
        )
