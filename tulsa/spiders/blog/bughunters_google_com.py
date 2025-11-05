import json
from datetime import datetime
from time import mktime
from typing import override
from urllib.parse import urljoin

from crawlee import Request
from crawlee.crawlers import HttpCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog


async def default_request_handler(context: HttpCrawlingContext):
    for entry in json.loads(await context.http_response.read())["items"]:
        # Entry can be null
        if not entry:
            continue
        title = entry["title"]
        url = urljoin(context.request.loaded_url or context.request.url, entry["href"])
        published = entry["publishDate"]
        description = entry["description"]

        item = Blog(url=url, title=title)
        item.description = description
        item.published = datetime.fromtimestamp(mktime(parse_date(published)))  # pyright: ignore [reportArgumentType]

        context.log.info(item)
        yield item


class BughuntersGoogleComSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                Request.from_url(
                    "https://bughunters.google.com/rest/v1/articles/search",
                    method="POST",
                    payload=json.dumps(
                        {
                            "blogTagSlugs": [],
                            "category": "blog",
                            "language": "en",
                            "order": "DESC",
                            "pageIndex": 0,
                            "pageSize": 20,
                            "sort": "published",
                        }
                    ),
                )
            ]
        )
