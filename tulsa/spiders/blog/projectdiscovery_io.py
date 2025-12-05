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


class ProjectdiscoveryIoSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                Request.from_url(
                    "https://projectdiscovery.io/blog/stories/1", headers={"Rsc": "1"}
                )
            ]
        )

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        res = (await context.http_response.read()).decode()
        pos = res.find("f:[")
        json_data = res[pos + 2 :]
        items = json.loads(json_data)[3]["children"][1][3]["children"][0][3][
            "children"
        ][3]["stories"]

        if len(items) == 0:
            context.log.error(f"{context.request.url} | Cannot find stories")
            return

        for entry in items:
            title = entry["title"]
            url = f"https://projectdiscovery.io/blog/{entry['slug']}"
            published = parse_date(entry["published_at"])
            thumbnail = entry["feature_image"]
            # TODO: the description needs to be ...
            description = entry["excerpt"]

            item = Blog(url=url, title=title)
            item.description = description
            item.thumbnail = thumbnail
            if published:
                item.published = datetime.fromtimestamp(mktime(published))

            yield item
