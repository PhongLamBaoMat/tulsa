import json
from datetime import datetime
from time import mktime
from typing import override

from crawlee import Request
from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog, Category


class HalbornComSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                Request.from_url(
                    "https://www.halborn.com/blog/1?filter=article",
                    headers={"Rsc": "1"},
                )
            ]
        )

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        res = (await context.http_response.read()).decode()
        pos = res.rfind("2:[")
        json_data = res[pos + 2 :]
        j = json.loads(json_data)
        items = j[0][3]["data"]["articles"]["data"]

        if len(items) == 0:
            context.log.error(f"{context.request.url} | Cannot find articles data")
            return

        for entry in items:
            entry = entry["attributes"]
            title = entry["Title"]
            url = f"https://www.halborn.com/blog/post/{entry['Slug']}"
            published = parse_date(entry["publishedAt"])
            description = entry["Description"]
            thumbnail = entry["MetaImage"]["data"]["attributes"]["formats"]["medium"][
                "url"
            ]

            item = Blog(url=url, title=title)
            item.description = description
            item.thumbnail = thumbnail
            if published:
                item.published = datetime.fromtimestamp(mktime(published))
            item.category = Category.BugBounty

            yield item
