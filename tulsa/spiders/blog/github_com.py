import json
import os
from datetime import datetime
from time import mktime
from typing import final, override

from crawlee import Request
from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog


@final
class GoogleSecurityResearchSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)
        token = os.getenv("GITHUB_ADVISORY_API_TOKEN")
        if not token or len(token) == 0:
            raise ValueError(
                "GITHUB_ADVISORY_API_TOKEN environment variable is not set"
            )
        self.token = token

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                Request.from_url(
                    "https://api.github.com/repos/google/security-research/security-advisories",
                    headers={
                        "Accept": "application/vnd.github+json",
                        "Authorization": f"Bearer {self.token}",
                        "X-GitHub-Api-Version": "2022-11-28",
                    },
                )
            ]
        )

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        items = json.loads(await context.http_response.read())
        for cve in items:
            cve_id = cve.get("cve_id")
            title = cve.get("summary")
            title = f"{cve_id}: {title}" if cve_id else title
            url = cve.get("html_url")
            summary = cve.get("description")
            published = parse_date(cve.get("published_at"))
            author = "Google Security Research"

            item = Blog(url=url, title=title)
            item.description = summary[:1000]
            item.author = author
            if published:
                item.published = datetime.fromtimestamp(mktime(published))

            yield item
