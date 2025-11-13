import json
from datetime import datetime
from time import mktime
from typing import override

from bs4 import BeautifulSoup
from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import HtmlSpider
from tulsa.helpers import parse_date
from tulsa.models import Blog


async def default_request_handler(context: ParselCrawlingContext):
    items = json.loads(await context.http_response.read())["items"]

    for entry in items:
        title = entry["title"]
        url = f"https://www.sonicwall.com/blog{entry['url']}"
        description = BeautifulSoup(entry["paragraph"], "lxml").text[:1000]
        published = parse_date(entry["published_date"])

        item = Blog(url=url, title=title)
        item.description = description
        if published:
            item.published = datetime.fromtimestamp(mktime(published))

        context.log.info(item)
        yield item


class CaturelabsSonicwallComSpider(HtmlSpider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                "https://www.sonicwall.com/api/content?contentKey=security-news&page=0&pageSize=20&locale=en-us"
            ]
        )
