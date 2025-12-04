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


class AuditsBlockHacksIoSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                Request.from_url(
                    "https://audits.blockhacks.io/api/posts",
                    headers={
                        "Referer": "https://audits.blockhacks.io/",
                        "Priority": "u=1, i",
                    },
                )
            ]
        )

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        data = json.loads(await context.http_response.read())
        for entry in data:
            url = f"https://audits.blockhacks.io/audit/{entry['id']}"
            title = entry["title"]
            description = entry["description"]
            published = parse_date(
                entry.get("created_at") or entry.get("updated_at") or ""
            )

            item = Blog(url=url, title=title)
            item.description = description
            item.category = Category.Blockchain
            if published:
                item.published = datetime.fromtimestamp(mktime(published))

            yield item
