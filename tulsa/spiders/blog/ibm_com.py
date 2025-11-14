import json
from collections.abc import AsyncIterator
from cProfile import label
from datetime import datetime
from time import mktime
from typing import override
from urllib.parse import urljoin

from crawlee import Request
from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics
from tldextract.tldextract import PUBLIC_SUFFIX_LIST_URLS

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog


class IbmComSpider(Spider):
    def __init__(self):
        super().__init__(default_request_handler=self.default_request_handler)

    @staticmethod
    async def default_request_handler(
        context: ParselCrawlingContext,
    ) -> AsyncIterator[Blog]:
        res = json.loads(await context.http_response.read())
        for entry in res["body"]["articleList"]:
            title = entry["title"]
            url = entry["link"]
            description = entry["description"]
            thumbnail = entry["imageCrops"].get(
                "crop-thumbnail-16-by-9-retina"
            ) or entry["imageCrops"].get("crop-thumbnail-2-by-1-retina")
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

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                "https://www.ibm.com/content/adobe-cms/us/en/think/x-force"
                + "/jcr:content/root/table_of_contents/horizontal_media_gro.api.json?pageNum=1&itemsPerPage=15"
            ]
        )


class ResearchIbmComSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)
        self.router._handlers_by_label["fetch_articles"] = self.fetch_articles  # pyright: ignore [reportPrivateUsage]

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        item = Blog.from_html_selector(context.selector)
        if not item:
            context.log.error(
                f"{context.request.url} | Cannot find url or title HTML element"
            )
            return
        if not item.published:
            published = context.selector.xpath(".//time/@datetime").get()
            if published:
                published = parse_date(published)
                if published:
                    item.published = datetime.fromtimestamp(mktime(published))
        # TODO: item.description can be more details
        yield item

    @staticmethod
    async def fetch_articles(context: ParselCrawlingContext):
        items = (
            context.selector.xpath(
                '//article[@class="JFHpL lXICR yLUcM undefined" or @class="E5NKX SdMhc sceKP"]'
            )
            .xpath(".//h3/a/@href")
            .getall()
        )
        if len(items) == 0:
            context.log.error(f"{context.request.url} | Cannot find HTML element")
            return
        await context.add_requests(
            [
                Request.from_url(
                    urljoin(context.request.loaded_url or context.request.url, url)
                )
                for url in items
            ]
        )

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                Request.from_url(url, label="fetch_articles")
                for url in [
                    "https://research.ibm.com/topics/security",
                    "https://research.ibm.com/topics/threat-management",
                ]
            ]
        )
