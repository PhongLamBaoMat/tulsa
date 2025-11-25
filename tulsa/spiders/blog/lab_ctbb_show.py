import html
import json
from datetime import datetime
from time import mktime
from typing import override
from urllib.parse import urljoin

from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog


class LabCtbbShowSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(["https://lab.ctbb.show/research/articles.json"])

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        for entry in json.loads(await context.http_response.read()):
            title = entry["title"]
            url = urljoin(
                context.request.loaded_url or context.request.url, entry["url"]
            )
            description = entry.get("description") or entry.get("summary")
            publised = entry.get("date")

            item = Blog(url=url, title=html.unescape(title))
            if description:
                item.description = html.unescape(description)
            if publised:
                published = parse_date(publised)
                if published:
                    item.published = datetime.fromtimestamp(mktime(published))

            yield item
