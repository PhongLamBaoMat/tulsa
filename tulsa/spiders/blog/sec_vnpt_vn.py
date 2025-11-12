import json
from datetime import datetime
from time import mktime
from typing import override
from urllib.parse import urljoin

from crawlee import Request
from crawlee.crawlers import HttpCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog


async def default_request_handler(context: HttpCrawlingContext):
    items = json.loads(await context.http_response.read())["data"]["posts"]

    for entry in items:
        title = entry["title"]
        published = parse_date(entry["created_at"])
        if not published:
            continue
        url = f"https://sec.vnpt.vn/{published.tm_year}/{published.tm_mon}/{entry['slug']}"
        description = entry["first_200_words"]
        thumbnail = entry["thumbnail"]

        item = Blog(url=url, title=title)
        item.description = description
        item.thumbnail = thumbnail
        item.published = datetime.fromtimestamp(mktime(published))

        yield item


class SecVpnptVnSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                Request.from_url(
                    "https://sec.vnpt.vn/api/post/list/?page=1&limit=12",
                )
            ]
        )
