import json
import os
import re
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from time import mktime
from typing import final, override

from crawlee import Request
from crawlee.crawlers import HttpCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Cve

_GITHUB_NEXT_PAGE = re.compile(r'(?<=<)([\S]*)(?=>; rel="next")')


async def default_handler(context: HttpCrawlingContext) -> AsyncIterator[Cve]:
    next_page = context.http_response.headers.get("link")
    if next_page:
        await context.add_requests(_GITHUB_NEXT_PAGE.findall(next_page))

    res = json.loads(await context.http_response.read())
    for cve in res:
        cve_id = cve.get("cve_id") or cve.get("ghsa_id")
        url = cve.get("html_url")
        summary = cve.get("summary") or cve.get("description")
        published = cve.get("published_at")
        score = cve["cvss"].get("score") or 0.0
        cna = "Github Advisory Database"

        if not published:
            context.log.error(f"{cve_id} doesn't have published date.")
            continue

        date = parse_date(published)
        if not date:
            context.log.error(f"Cannot parse '{published}' for CVE id: {cve_id}")
            continue
        published = datetime.fromtimestamp(mktime(date))

        item = Cve(id=cve_id, url=url, published=published)
        if summary:
            item.description = summary[:1000]
        item.score = score
        item.cna = cna

        yield item


@final
class GithubCveSpider(Spider):
    from_published: str
    token: str

    def __init__(self, from_published: datetime | None = None):
        super().__init__(default_request_handler=default_handler)
        if not from_published:
            from_published = datetime.fromtimestamp(
                datetime.now(UTC).timestamp() - 60 * 60 * 24 * 7
            )
        token = os.getenv("GITHUB_ADVISORY_API_TOKEN")
        if not token:
            raise ValueError(
                "GITHUB_ADVISORY_API_TOKEN environment variable is not set"
            )
        self.token = token
        self.from_published = from_published.strftime("%Y-%m-%dT%H:%M:%SZ")

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        url = "https://api.github.com/advisories"
        url += f"?type=reviewed&published=>{self.from_published}"
        request = Request.from_url(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )

        return await super().run([request])
