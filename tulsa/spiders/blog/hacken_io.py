import json
from typing import override
from urllib.parse import urljoin

from crawlee import Request
from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.models import Blog, Category


class HackenIoSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)
        self.router._handlers_by_label["fetch_articles"] = self.fetch_articles  # pyright: ignore [reportPrivateUsage]

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                Request.from_url(url, label="fetch_articles")
                for url in [
                    "https://hacken.io/category/case-studies/",
                    "https://hacken.io/category/reports/",
                ]
            ]
        )

    @staticmethod
    async def fetch_articles(context: ParselCrawlingContext):
        items = (
            context.selector.xpath('//li[@data-sentry-component="BlogArticleCard"]')
            .xpath(".//a/@href")
            .getall()
        )

        if len(items) == 0:
            context.log.error(f"{context.request.url} | Cannot find HTML element")
            return

        await context.add_requests(
            [
                urljoin(context.request.loaded_url or context.request.url, url)
                for url in items
            ]
        )

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        data = context.selector.xpath(
            '/html/head/meta[@name="application/ld+json"]/@content'
        ).get()
        if not data:
            context.log.error(f"{context.request.url} | Cannot find json schema")
            return

        item = None
        for entry in json.loads(data)["@graph"]:
            if entry["@type"] == "Article":
                item = Blog.from_json_schema(entry)
                break

        if not item:
            context.log.error(
                f"{context.request.url} | Cannot find title or url element"
            )
            return
        item.category = Category.Blockchain

        yield item
