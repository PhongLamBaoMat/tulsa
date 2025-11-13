from collections.abc import AsyncIterator
from datetime import datetime
from time import mktime
from typing import override
from urllib.parse import urljoin

from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog


async def default_request_handler(
    context: ParselCrawlingContext,
) -> AsyncIterator[Blog]:
    latest_entry = context.selector.xpath('//div[@class="rounded-2xl bg-gray-100 p-6"]')
    # https://www.securitum.com/pentest-chronicles.html has different HTML element layout
    # We have to change the `latest_entry` to get the url
    if not latest_entry.xpath(".//a/@href").get():
        latest_entry = context.selector.xpath(
            '//section[@class="container mx-auto max-w-6xl px-4 mb-12"]'
        )
    title = latest_entry.xpath(".//h2/text()").get()
    if not title:
        context.log.error(f"{context.request.url} | Cannot find title HTML element")
        return
    url = latest_entry.xpath(".//a/@href").get()
    if not url:
        context.log.error(f"{context.request.url} | Cannot find url HTML element")
        return
    url = urljoin(context.request.loaded_url or context.request.url, url)
    description = latest_entry.xpath(
        './/p[@class="text-gray-800 text-lg font-normal"]/text()'
    ).get()
    thumbnail = latest_entry.xpath(".//img/@src").get()
    published = latest_entry.xpath(
        './/h1[@class="text-gray-500 font-normal"]/text()'
    ).get()
    item = Blog(url=url, title=title)
    if description:
        item.description = description.strip()
    if thumbnail:
        item.thumbnail = urljoin(
            context.request.loaded_url or context.request.url, thumbnail
        )
    if published:
        published = parse_date(published)
        if published:
            item.published = datetime.fromtimestamp(mktime(published))
    yield item

    for entry in context.selector.xpath(
        '//div[@class="flex flex-col md:flex-row gap-4 py-6 border-b border-gray-200"]'
    ):
        title = entry.xpath(".//h2/text()").get()
        if not title:
            context.log.error(f"{context.request.url} | Cannot find title HTML element")
            return
        url = entry.xpath(".//a/@href").get()
        if not url:
            context.log.error(f"{context.request.url} | Cannot find url HTML element")
            return
        url = urljoin(context.request.loaded_url or context.request.url, url)
        description = (
            entry.xpath('.//p[@class="text-gray-800 text-md font-normal"]/text()').get()
            or entry.xpath(
                './/p[@class="text-gray-800 text-md font-normal py-4"]/text()'
            ).get()
        )
        thumbnail = entry.xpath(".//img/@src").get()
        published = entry.xpath(
            './/h1[@class="text-gray-500 font-normal"]/text()'
        ).get()

        item = Blog(url=url, title=title)
        if description:
            item.description = description
        if thumbnail:
            item.thumbnail = urljoin(
                context.request.loaded_url or context.request.url, thumbnail
            )
        if published:
            published = parse_date(published)
            if published:
                item.published = datetime.fromtimestamp(mktime(published))

        yield item


class SecuritumComSpider(Spider):
    def __init__(self):
        super().__init__(default_request_handler=default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                "https://www.securitum.com/insights.html",
                "https://www.securitum.com/pentest-chronicles.html",
            ]
        )
