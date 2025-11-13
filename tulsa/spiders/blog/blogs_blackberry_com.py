import json
import re
from datetime import datetime
from time import mktime
from typing import override
from urllib.parse import urljoin

from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog

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


async def default_request_handler(context: ParselCrawlingContext):
    for entry in json.loads(await context.http_response.read()):
        title = entry["title"]
        url = entry["url"]
        published = entry["publishDate"]
        m = re.match(
            r"(\w{3}) (\d{1,2}), (\d{4}), (\d{1,2}):(\d{2}):(\d{2}) (AM|PM)", published
        )
        if not m:
            raise ValueError(f"Failed to parsed '{published}': {context.request.url}")
        month = month_dict[m.group(1)]
        day = m.group(2)
        year = m.group(3)
        hour = m.group(4)
        minute = m.group(5)
        second = m.group(6)
        if m.group(7) == "PM":
            hour = int(hour) + 12
        description = entry["excerpt"]
        thumbnail = entry["thumbnail"]

        item = Blog(url=url, title=title)
        item.description = description
        item.published = datetime.fromtimestamp(
            mktime(parse_date(f"{year}-{month}-{day}T{hour}:{minute}:{second}+00:00"))  # pyright: ignore [reportArgumentType]
        )
        item.thumbnail = urljoin(
            context.request.loaded_url or context.request.url, thumbnail
        )

        yield item


class BlogsBlackberryComSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                "https://blogs.blackberry.com/bin/blogs?page=1&category="
                + "https://blogs.blackberry.com/en/category/research-and-intelligence&locale=en"
            ]
        )
