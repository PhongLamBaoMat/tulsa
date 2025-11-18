import json
from datetime import datetime
from typing import override

from crawlee import Request
from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.models import Blog


class IssuesChromiumOrgSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)
        self.router._handlers_by_label["fetch_articles"] = self.fetch_articles  # pyright: ignore [reportPrivateUsage]

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                Request.from_url(
                    "https://issues.chromium.org/action/issues/list",
                    method="POST",
                    payload='[null,null,null,null,null,["157"],["hotlistid:5432630 status:(open | new | assigned | accepted | closed | fixed | verified | intended_behavior)",null,20,"start_index:0"]]',
                    headers={"Content-Type": "application/json"},
                    label="fetch_articles",
                )
            ]
        )

    @staticmethod
    async def fetch_articles(context: ParselCrawlingContext):
        data = json.loads((await context.http_response.read()).split(b"\n")[-1])
        ids = [e[1] for e in data[0][6][0]]

        await context.add_requests(
            [
                Request.from_url(
                    "https://issues.chromium.org/action/issues/batch",
                    method="POST",
                    headers={"Content-Type": "application/json"},
                    payload=f'["b.BatchGetIssuesRequest",null,null,[{ids},2,1]]',
                )
            ]
        )

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        data = json.loads((await context.http_response.read()).split(b"\n")[-1])
        for entry in data[0][2][0]:
            url = f"https://issues.chromium.org/issues/{entry[1]}"
            title = entry[2][5]
            description = entry[43][0][:1000]
            published = datetime.fromtimestamp(entry[5][0])

            item = Blog(url=url, title=title)
            item.description = description
            item.published = published

            yield item


class ProjectZeroIssueTracker(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)
        self.router._handlers_by_label["fetch_articles"] = self.fetch_articles  # pyright: ignore [reportPrivateUsage]

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                Request.from_url(
                    "https://project-zero.issues.chromium.org/action/issues/list",
                    method="POST",
                    payload='[null,null,null,null,null,["365"],["status:(open | new | accepted | closed | fixed | verified)",null,20,"start_index:0"]]',
                    headers={"Content-Type": "application/json"},
                    label="fetch_articles",
                )
            ]
        )

    @staticmethod
    async def fetch_articles(context: ParselCrawlingContext):
        data = json.loads((await context.http_response.read()).split(b"\n")[-1])
        ids = [e[1] for e in data[0][6][0]]

        await context.add_requests(
            [
                Request.from_url(
                    "https://project-zero.issues.chromium.org/action/issues/batch",
                    method="POST",
                    headers={"Content-Type": "application/json"},
                    payload=f'["b.BatchGetIssuesRequest",null,null,[{ids},2,1]]',
                )
            ]
        )

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        data = json.loads((await context.http_response.read()).split(b"\n")[-1])
        for entry in data[0][2][0]:
            url = f"https://project-zero.issues.chromium.org/issues/{entry[1]}"
            title = entry[2][5]
            description = entry[43][0][:1000]
            published = datetime.fromtimestamp(entry[5][0])

            item = Blog(url=url, title=title)
            item.description = description
            item.published = published

            yield item
