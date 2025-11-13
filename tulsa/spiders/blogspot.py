import json
import os
from collections.abc import AsyncIterator
from datetime import datetime
from time import mktime
from typing import TypedDict, cast, final, override

from bs4 import BeautifulSoup
from crawlee import ConcurrencySettings, Request
from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import is_valid_url, parse_date
from tulsa.models import Blog, Category


class BlogspotProperties(TypedDict):
    category: Category


async def default_handler(context: ParselCrawlingContext) -> AsyncIterator[Blog]:
    user_data = cast(BlogspotProperties, context.request.user_data)  # pyright: ignore [reportInvalidCast]
    res = json.loads(await context.http_response.read())
    for entry in res["items"]:
        title = entry["title"]
        url = entry["url"]
        category = user_data.get("category", Category.Generic)
        published = entry["published"]
        images = entry.get("images", [])
        summary = entry.get("content")

        item = Blog(url=url, title=title, category=category)
        published = parse_date(published)
        if published:
            item.published = datetime.fromtimestamp(mktime(published))
        for image in images:
            if is_valid_url(image["url"]):
                item.thumbnail = image["url"]
                break

        if summary:
            item.description = BeautifulSoup(summary, "html.parser").text[:1000]

        yield item


async def prefetch_url(context: ParselCrawlingContext):
    max_items = context.request.user_data.get("max_items", 20)  # pyright: ignore [reportUnknownMemberType, reportUnknownVariableType]
    if not context.request.user_data.get("token"):  # pyright: ignore [reportUnknownMemberType]
        raise ValueError("Missing `token` field.")
    token = context.request.user_data.get("token")  # pyright: ignore [reportUnknownMemberType, reportUnknownVariableType]

    res = json.loads(await context.http_response.read())
    url = f"{res['posts']['selfLink']}?fetchBodies=true&fetchImages=true"
    url += f"&maxResults={max_items}&key={token}"

    await context.add_requests([url])


@final
class BlogspotSpider(Spider):
    def __init__(self, requests: list[Request]):
        concurrency_settings = ConcurrencySettings(max_tasks_per_minute=30)
        super().__init__(
            default_request_handler=default_handler,
            concurrency_settings=concurrency_settings,
        )
        self.router._handlers_by_label["prefetch"] = prefetch_url  # pyright: ignore [reportPrivateUsage]
        token = os.getenv("BLOGSPOT_API_TOKEN")
        if not token:
            raise ValueError("BLOGSPOT_API_TOKEN environment variable is not set")
        for r in requests:
            r.url = f"https://www.googleapis.com/blogger/v3/blogs/byurl?url={r.url}&key={token}"
            r.user_data["token"] = token  # pyright: ignore [reportUnknownMemberType]
            r.user_data["max_items"] = 20  # pyright: ignore [reportUnknownMemberType]
            r.user_data["label"] = "prefetch"  # pyright: ignore [reportUnknownMemberType]
        self.requests = requests

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(self.requests)
