import json
from datetime import datetime
from time import mktime
from typing import override

from bs4 import BeautifulSoup
from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog


class SocketDevSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(["https://socket.dev/api/blog/feed.json"])

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        items = json.loads(await context.http_response.read())["items"]

        if len(items) == 0:
            context.log.error(f"{context.request.url} | Items are empty")
            return

        for entry in items:
            title = entry["title"]
            url = entry["url"]
            published = entry.get("date_published")
            description = entry.get("summary") or entry.get("content_html")
            thumbnail = entry.get("image") or entry.get("banner_image")

            item = Blog(url=url.replace("?utm_medium=feed", ""), title=title)
            if description:
                item.description = BeautifulSoup(description, "lxml").text[:1000]
            if thumbnail:
                item.thumbnail = thumbnail
            if published:
                published = parse_date(published)
                if published:
                    item.published = datetime.fromtimestamp(mktime(published))

            yield item
