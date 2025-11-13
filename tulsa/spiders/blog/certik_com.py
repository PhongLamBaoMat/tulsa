import json
from datetime import datetime
from time import mktime
from typing import override
from urllib.parse import urljoin

from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog, Category


async def default_request_handler(context: ParselCrawlingContext):
    data = context.selector.xpath(
        '//script[@id="__NEXT_DATA__" and @type="application/json"]/text()'
    ).get()
    if not data:
        context.log.error(
            f"{context.request.url} | Cannot find __NEXT_DATA__ HTML element"
        )
        return

    items = json.loads(data)["props"]["pageProps"]["blogSpotlightArticle"]["items"]

    for entry in items:
        title = entry["title"]
        url = f"https://www.certik.com/resources/blog/{entry['pageSlug']}"
        published = entry["postDate"]
        description = entry["summary"]
        thumbnail = entry["mainImageUrl"]

        item = Blog(url=url, title=title, category=Category.Blockchain)
        item.description = description
        item.thumbnail = urljoin(
            context.request.loaded_url or context.request.url, thumbnail
        )
        item.published = datetime.fromtimestamp(mktime(parse_date(published)))  # pyright: ignore [reportArgumentType]

        yield item


class CertikComSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(["https://www.certik.com/resources/blog"])
