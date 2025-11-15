import json
from datetime import datetime
from time import mktime
from typing import override
from urllib.parse import urljoin

from crawlee import Request
from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog


class EshardComSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                Request.from_url(
                    "https://cms.eshard.com/graphql",
                    method="POST",
                    payload=json.dumps(
                        {
                            "variables": {"limit": 10, "start": 0},
                            "query": 'query ($limit: Int!, $start: Int!) {\n  articlesConnection(limit: $limit, start: $start, sort: "datePublication:desc") {\n    values {\n      categories_articles {\n        id\n        name\n        __typename\n      }\n      slug\n      datePublication\n      title\n      cover {\n        ... on UploadFile {\n          url\n          width\n          height\n          alternativeText\n          caption\n          formats\n          __typename\n        }\n        __typename\n      }\n      content\n      author {\n        firstname\n        lastname\n        image {\n          ... on UploadFile {\n            url\n            width\n            height\n            alternativeText\n            caption\n            formats\n            __typename\n          }\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    aggregate {\n      totalCount\n      count\n      __typename\n    }\n    __typename\n  }\n}\n',
                        }
                    ),
                    headers={"Content-Type": "application/json"},
                )
            ]
        )

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        items = json.loads(await context.http_response.read())["data"][
            "articlesConnection"
        ]["values"]

        if len(items) == 0:
            context.log.error(f"{context.request.url}| Cannot find posts")
            return

        for entry in items:
            should_skip = False
            for category in entry["categories_articles"]:
                if category["name"] == "Corporate News":
                    should_skip = True
                    break
            if should_skip:
                continue
            title = entry["title"]
            url = f"https://eshard.com/posts/{entry['slug']}"
            published = parse_date(entry["datePublication"])
            description = entry["content"]
            thumbnail = (
                entry["cover"]["url"]
                if entry["cover"]["url"].endswith(".png")
                or entry["cover"]["url"].endswith(".jpg")
                else None
            )

            item = Blog(url=url, title=title)
            if description:
                item.description = description[:1000]
            if thumbnail:
                item.thumbnail = urljoin(
                    context.request.loaded_url or context.request.url, thumbnail
                )
            if published:
                item.published = datetime.fromtimestamp(mktime(published))

            yield item
