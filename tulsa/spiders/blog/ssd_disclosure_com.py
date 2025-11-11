from datetime import datetime
from time import mktime
from typing import override

import feedparser
from bs4 import BeautifulSoup
from crawlee.crawlers import HttpCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.models import Blog


async def default_request_handler(context: HttpCrawlingContext):
    entries = feedparser.parse(await context.http_response.read()).entries
    if len(entries) == 0:
        context.log.error(f"'{context.request.url}' doesn't have any entries to read")
        return

    for entry in entries:
        url = entry["link"]
        title = entry["title"]
        description = entry.get("summary")
        published = entry.get("published_parsed")

        item = Blog(url=url, title=title)
        if description:
            item.description = BeautifulSoup(description, "html.parser").text
        if published:
            item.published = datetime.fromtimestamp(mktime(published))

        yield item


class SsddisclosureComSpider(Spider):
    def __init__(self):
        super().__init__(
            default_request_handler=default_request_handler, allow_redirects=False
        )

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(["https://ssd-disclosure.com/feed/"])
