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


class CriminalipIoSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                "https://www.criminalip.io/api/blog/private?_fields=title,link,excerpt,jetpack_featured_media_url,date&categories=2239&per_page=12"
            ]
        )

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        items = json.loads(await context.http_response.read())

        for entry in items:
            url = entry["link"]
            title = entry["title"]["rendered"]
            description = BeautifulSoup(entry["excerpt"]["rendered"]).text
            thumbnail = entry["jetpack_featured_media_url"]
            published = parse_date(entry["date"])

            item = Blog(url=url, title=title.replace("\xa0", " ").strip())
            item.description = description.replace("\xa0", " ")
            item.thumbnail = thumbnail
            if published:
                item.published = datetime.fromtimestamp(mktime(published))

            yield item
