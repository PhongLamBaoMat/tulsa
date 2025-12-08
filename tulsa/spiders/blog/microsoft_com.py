import html
import json
from datetime import datetime
from time import mktime
from typing import override

from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog


class MsrcMicrosoftComSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                "https://www.microsoft.com/msstoreapiprod/api/msrc/Search?pageType=blog&top=10"
            ]
        )

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        items = json.loads(await context.http_response.read())["results"]

        for entry in items:
            title = entry["title"]
            url = f"https://www.microsoft.com{entry['permalink']}"
            description = html.unescape(entry["blurb"])
            published = parse_date(entry["publishedDate"])

            item = Blog(url=url, title=title)
            item.description = description
            if published:
                item.published = datetime.fromtimestamp(mktime(published))

            yield item
