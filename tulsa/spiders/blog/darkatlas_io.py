import json
from datetime import datetime
from time import mktime
from typing import override

from bs4 import BeautifulSoup
from crawlee import Request
from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog


class DarkatlasIoSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        categories = ["malware-analysis", "threat-intelligence"]
        return await super().run(
            [
                Request.from_url(
                    "https://blog-wp.darkatlas.io/graphql",
                    method="POST",
                    payload=json.dumps(
                        {
                            "query": "\n  query POSTS($first: Int, $after: String, $categorySlug: String, $search: String) {\n    posts (first: $first, after: $after , where : {\n      categoryName: $categorySlug,\n      search: $search\n    }) {\n      nodes {\n        title\n        id\n        excerpt\n        slug\n        date\n        featuredImage {\n          node {\n            altText\n            link\n          }\n        }\n        tags {\n          nodes {\n            slug\n            name\n          }\n        }\n        acfPost {\n         readTime\n      }\n        categories {\n          nodes {\n            id\n            slug\n            name\n            link\n            uri\n            \n          }\n        }\n      } \n      pageInfo {\n        startCursor\n        endCursor\n        hasPreviousPage\n        hasNextPage\n      }\n    }\n  }\n",
                            "variables": {
                                "first": 10,
                                "categorySlug": category,
                                "search": "",
                            },
                            "operationName": "POSTS",
                        }
                    ),
                    headers={"Content-Type": "application/json"},
                    use_extended_unique_key=True,
                )
                for category in categories
            ]
        )

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        items = json.loads(await context.http_response.read())["data"]["posts"]["nodes"]

        for entry in items:
            title = entry["title"]
            url = f"https://darkatlas.io/blog/{entry['slug']}"
            published = parse_date(entry["date"])
            description = entry["excerpt"]
            thumbnail = entry["featuredImage"]
            if thumbnail:
                thumbnail = thumbnail["node"]["link"]

            item = Blog(url=url, title=title)
            item.description = BeautifulSoup(description, "lxml").text
            item.thumbnail = thumbnail
            if published:
                item.published = datetime.fromtimestamp(mktime(published))

            yield item
