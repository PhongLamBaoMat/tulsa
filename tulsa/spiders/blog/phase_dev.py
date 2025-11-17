import json
from datetime import datetime
from time import mktime
from typing import override
from urllib.parse import urljoin

from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog


class PhaseDevSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(["https://phase.dev/blog/"])

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        data = context.selector.xpath(
            '//script[@id="__NEXT_DATA__" and @type="application/json"]/text()'
        ).get()
        if not data:
            context.log.error(f"{context.request.url} | Cannot find HTML element")
            return

        items = json.loads(data)["props"]["pageProps"]["posts"]
        if len(items) == 0:
            context.log.error(f"{context.request.url} | Posts are empty")
            return

        for entry in items:
            title = entry["frontmatter"]["title"]
            url = f"https://phase.dev/blog/{entry['slug']}"
            description = entry["frontmatter"]["subtitle"]
            thumbnail = entry["frontmatter"].get("coverImage")
            published = entry["frontmatter"].get("date")

            item = Blog(url=url, title=title)
            item.description = description
            if thumbnail:
                item.thumbnail = urljoin(
                    context.request.loaded_url or context.request.url,
                    thumbnail,
                )
            if published:
                published = parse_date(published)
                if published:
                    item.published = datetime.fromtimestamp(mktime(published))

            yield item
