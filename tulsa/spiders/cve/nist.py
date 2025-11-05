import json
import logging
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from time import mktime
from typing import final, override

from crawlee import ConcurrencySettings
from crawlee.crawlers import HttpCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Cve


async def default_handler(context: HttpCrawlingContext) -> AsyncIterator[Cve]:
    logger = logging.getLogger(__name__)
    res = json.loads(await context.http_response.read())
    for vuln in res.get("vulnerabilities", []):
        cve = vuln["cve"]
        score = 0.0
        # The CVE got rejected, we skip it
        if cve["vulnStatus"] == "Rejected":
            continue
        for value in cve["metrics"].values():
            score = value[0]["cvssData"]["baseScore"]
            break
        cve_id = cve["id"]
        description = cve["descriptions"][0]["value"]
        url = f"https://nvd.nist.gov/vuln/detail/{cve['id']}"
        cna = cve.get("sourceIdentifier")
        published = cve.get("published")

        if not published:
            logger.error(f"{cve_id} doesn't have published date.")
            continue

        date = parse_date(published)
        if not date:
            logger.error(f"Cannot parse '{published}' for CVE id: {cve_id}")
            continue
        published = datetime.fromtimestamp(mktime(date))

        item = Cve(id=cve_id, url=url, published=published)
        item.score = score
        item.description = description
        if cna:
            item.cna = cna

        yield item

    total_results = res["totalResults"]
    results_per_page = res["resultsPerPage"]
    next_index = res["startIndex"] + results_per_page

    # We'll continue to crawl the next page
    if next_index < total_results and context.request.loaded_url:
        pos = context.request.loaded_url.find("&startIndex=")
        url = (
            f"{context.request.loaded_url}&startIndex={next_index}"
            if pos == -1
            else f"{context.request.loaded_url[:pos]}&startIndex={next_index}"
        )
        await context.add_requests([url])


@final
class NistCveSpider(Spider):
    def __init__(self, from_published: datetime | None = None):
        concurreny_settings = ConcurrencySettings(
            min_concurrency=1,
            max_concurrency=1,
            max_tasks_per_minute=5,
            desired_concurrency=1,
        )
        super().__init__(
            default_request_handler=default_handler,
            concurrency_settings=concurreny_settings,
        )
        if not from_published:
            from_published = datetime.fromtimestamp(
                datetime.now(UTC).timestamp() - 60 * 60 * 24 * 7
            )
        self.from_published = from_published.strftime("%Y-%m-%dT%H:%M:%SZ")

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S")
        url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        url += f"/?noRejected&pubStartDate={self.from_published}&pubEndDate={now}"

        return await super().run([url])
