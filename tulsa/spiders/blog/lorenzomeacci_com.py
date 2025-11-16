import json
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


class LorenzomeacciComSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(["https://lorenzomeacci.com/blog-list"])

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        data = context.selector.xpath(
            '//astro-island[@prefix="v1" and @component-export="default"]/@props'
        ).get()

        if not data:
            context.log.error(f"{context.request.url} | Cannot find JSON props")
            return
        data = json.loads(data)
        items = data["pageData"][-1]["pages"][-1].items()

        if len(items) == 0:
            context.log.error(f"{context.request.url} | Empty page")
            return

        site_id = data["pageData"][-1]["siteId"][-1]

        for _, entry in items:
            entry = entry[-1]
            if entry.get("date") is None or entry.get("meta") is None:
                continue
            title = entry["meta"][-1]["title"][-1]
            url = urljoin(
                context.request.loaded_url or context.request.url, entry["slug"][-1]
            )
            published = parse_date(entry["date"][-1])
            description = entry["meta"][-1]["description"][-1]
            image_path = (
                entry["coverImagePath"][-1] or entry["meta"][-1]["ogImageOrigin"][-1]
            )

            item = Blog(url=url, title=title)
            item.description = BeautifulSoup(description, "lxml").text
            if image_path:
                item.thumbnail = f"https://assets.zyrosite.com/cdn-cgi/image/format=auto,w=328,h=197,fit=crop/{site_id}/{image_path}"
            if published:
                item.published = datetime.fromtimestamp(mktime(published))

            yield item
