from datetime import datetime
from time import mktime
from typing import override
from urllib.parse import urljoin

from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog


async def default_request_handler(context: ParselCrawlingContext):
    items = context.selector.xpath(
        '//div[@class="wp-block-group alignwide is-nowrap is-layout-flex wp-container-core-group-is-layout-2b175ab0 wp-block-group-is-layout-flex"]'
    )
    if len(items) == 0:
        context.log.error(f"{context.request.url} | Cannot find HTML element")
        return

    for entry in items:
        title = entry.xpath(".//h2//a/text()").get()
        if not title:
            continue
        url = entry.xpath(".//h2/a/@href").get()
        if not url:
            continue
        url = urljoin(context.request.loaded_url or context.request.url, url)
        description = entry.xpath(
            './/p[@class="wp-block-post-excerpt__excerpt"]/text()'
        ).get()
        published = entry.xpath(".//time/@datetime").get()

        item = Blog(url=url, title=title)

        if description:
            item.description = description.replace("\xa0", "").strip()
        if published:
            published = parse_date(published)
            if published:
                item.published = datetime.fromtimestamp(mktime(published))

        yield item


class SectemplatesSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(["https://www.sectemplates.com/"])
