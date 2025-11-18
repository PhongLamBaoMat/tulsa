from html.parser import HTMLParser
from typing import override

import feedparser
from crawlee import Request
from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import is_valid_url
from tulsa.models import Blog


class LinkFinder(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.__links: list[str] = []

    @override
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            for attr, value in attrs:
                if attr == "href" and value:
                    self.__links.append(value)

    @property
    def links(self) -> list[str]:
        return self.__links


class RedditComSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)
        self.router._handlers_by_label["fetch_articles"] = self.fetch_articles  # pyright: ignore [reportPrivateUsage]

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                Request.from_url(url, label="fetch_articles")
                for url in [
                    "https://www.reddit.com/r/netsec/new/.rss",
                    "https://www.reddit.com/r/ReverseEngineering/new/.rss",
                ]
            ]
        )

    @staticmethod
    async def fetch_articles(context: ParselCrawlingContext):
        requests: list[str] = []
        for entry in feedparser.parse(await context.http_response.read()).entries[:10]:
            content = entry["content"][0].value

            finder = LinkFinder()
            finder.feed(content)
            if is_valid_url(finder.links[1]):
                requests.append(finder.links[1])

        await context.add_requests(requests)

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        item = Blog.from_html_selector(context.selector)
        if item:
            item.title = item.title.removeprefix("Github - ")
            yield item
