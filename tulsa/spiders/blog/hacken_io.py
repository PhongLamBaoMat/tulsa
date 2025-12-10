import json
from datetime import datetime
from time import mktime
from typing import override

from crawlee import Request
from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics
from tulsa.helpers import parse_date
from tulsa.models import Blog, Category

from tulsa import Spider


class HackenIoSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                Request.from_url(url, headers={"Rsc": "1"})
                for url in [
                    "https://hacken.io/category/case-studies/",
                    "https://hacken.io/category/reports/",
                ]
            ]
        )

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        res = (await context.http_response.read()).decode()
        pos = res.rfind("2f:[")
        json_data = res[pos + 3 :].split("\n")[0]
        j = json.loads(json_data)
        items = j[1][3]["posts"]["list"]

        for entry in items:
            title = entry["title"]
            if "/case-studies/" in context.request.url:
                url = f"https://hacken.io/case-studies/{entry['slug']}"
            else:
                url = f"https://hacken.io/insights/{entry['slug']}"
            description = entry["excerpt"]
            thumbnail = entry["feature_image"]
            published = parse_date(entry["published_at"])

            item = Blog(url=url, title=title)
            item.description = description
            item.thumbnail = thumbnail
            if published:
                item.published = datetime.fromtimestamp(mktime(published))
            item.category = Category.Blockchain

            yield item
