import json
from datetime import datetime
from typing import override
from urllib.parse import urljoin

from crawlee.crawlers import HttpCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.models import Blog


async def default_request_handler(context: HttpCrawlingContext):
    for entry in json.loads(await context.http_response.read())["posts"]:
        if (
            entry["category"]["name"] != "security-research"
            and entry["category"]["name"] != "security"
        ):
            continue
        title = entry["title"]
        url = urljoin(context.request.loaded_url or context.request.url, entry["url"])
        if int(entry["publishTime"]) < 0:
            continue
        description = entry.get("description")
        published = datetime.fromtimestamp(int(entry["publishTime"]) / 1000)

        item = Blog(url=url, title=title)
        item.published = published
        if description:
            item.description = description

        context.log.info(item)
        yield item


class AkamaiComSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(["https://www.akamai.com/site/en/blog.blogsdata.json"])
