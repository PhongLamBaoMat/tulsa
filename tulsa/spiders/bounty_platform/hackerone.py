import base64
import json
import os
from collections.abc import AsyncIterator
from datetime import datetime
from time import mktime
from typing import override

from crawlee import Request
from crawlee.crawlers import HttpCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import HacktivityBounty, Severity


async def default_request_handler(
    context: HttpCrawlingContext,
) -> AsyncIterator[HacktivityBounty]:
    res = json.loads(await context.http_response.read())

    for report in res.get("data", []):
        url = report["attributes"].get("url")
        title = report["attributes"].get("title")
        published = report["attributes"].get("latest_disclosable_activity_at")
        awarded = report["attributes"].get("total_awarded_amount")
        severity = report["attributes"].get("severity_rating")

        item = HacktivityBounty(url=url, title=title)
        item.awarded = awarded
        item.severity = Severity(severity.lower()) if severity else None
        if published:
            published = parse_date(published)
            if published:
                item.published = datetime.fromtimestamp(mktime(published))
        relationships = report["relationships"]
        if relationships["program"]["data"]["attributes"].get("name"):
            item.program = relationships["program"]["data"]["attributes"]["name"]
        if relationships["reporter"]["data"]["attributes"].get("username"):
            item.reporter = relationships["reporter"]["data"]["attributes"]["username"]
        if relationships.get("report_generated_content"):
            if relationships["report_generated_content"]["data"]["attributes"].get(
                "hacktivity_summary"
            ):
                item.description = relationships["report_generated_content"]["data"][
                    "attributes"
                ]["hacktivity_summary"]

        yield item


class HackeroneHacktivitySpider(Spider):
    token: str

    def __init__(self):
        super().__init__(default_request_handler=default_request_handler)
        token = os.getenv("HACKERONE_API_TOKEN")
        if not token:
            raise ValueError("HACKERONE_API_TOKEN environment variable is not set")
        self.token = token

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                Request.from_url(
                    "https://api.hackerone.com/v1/hackers/hacktivity?queryString=disclosed:true&page[size]=25",
                    headers={
                        "Authorization": f"Basic {base64.b64encode(f'{self.token}'.encode()).decode()}",
                        "Accept": "application/json",
                    },
                )
            ]
        )
