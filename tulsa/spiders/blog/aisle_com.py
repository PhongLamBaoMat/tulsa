import json
from datetime import datetime
from time import mktime
from typing import override

from crawlee import Request
from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog


class AisleComSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [Request.from_url("https://aisle.com", headers={"Rsc": "1"})]
        )

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        res = (await context.http_response.read()).decode()
        pos = res.rfind("6:[")
        json_data = res[pos + 2 :]
        j = json.loads(json_data)
        items = j[3]["children"][6][3]["children"][3]["posts"]

        for entry in items:
            title = entry["title"]
            url = f"https://aisle.com/blog/{entry['slug']}"
            thumbnail = entry["heroImage"]["url"]
            published = parse_date(entry["publishedAt"])

            item = Blog(url=url, title=title)
            item.thumbnail = thumbnail
            if published:
                item.published = datetime.fromtimestamp(mktime(published))

            yield item
