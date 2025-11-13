import json
from collections.abc import AsyncIterator
from datetime import datetime
from time import mktime
from typing import override

from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog


async def default_request_handler(
    context: ParselCrawlingContext,
) -> AsyncIterator[Blog]:
    res = json.loads(await context.http_response.read())
    for entry in res["body"]["articleList"]:
        title = entry["title"]
        url = entry["link"]
        description = entry["description"]
        thumbnail = entry["imageCrops"].get("crop-thumbnail-16-by-9-retina") or entry[
            "imageCrops"
        ].get("crop-thumbnail-2-by-1-retina")
        published = entry["publishDate"]

        item = Blog(url=url, title=title)
        if description:
            item.description = description
        if thumbnail:
            item.thumbnail = thumbnail
        if published:
            published = parse_date(published)
            if published:
                item.published = datetime.fromtimestamp(mktime(published))

        yield item


class IbmSpider(Spider):
    def __init__(self):
        super().__init__(default_request_handler=default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                "https://www.ibm.com/content/adobe-cms/us/en/think/x-force"
                + "/jcr:content/root/table_of_contents/horizontal_media_gro.api.json?pageNum=1&itemsPerPage=15"
            ]
        )
