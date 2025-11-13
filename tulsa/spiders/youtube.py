import json
import os
from collections.abc import AsyncIterator
from datetime import datetime
from time import mktime
from typing import TypedDict, cast, final, override

from crawlee import Request
from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog, Category


class YoutubeProperties(TypedDict):
    category: Category


async def default_handler(context: ParselCrawlingContext) -> AsyncIterator[Blog]:
    res = json.loads(await context.http_response.read())
    user_data = cast(YoutubeProperties, context.request.user_data)  # pyright: ignore [reportInvalidCast]
    for entry in res.get("items", []):
        snippet = entry.get("snippet")
        if not snippet:
            continue
        if entry["id"]["kind"] != "youtube#video":
            continue
        title = snippet["title"]
        url = f"https://www.youtube.com/watch?v={entry['id']['videoId']}"
        category = user_data.get("category", Category.Generic)
        item = Blog(url=url, title=title, category=category)
        item.author = snippet["channelTitle"]
        item.description = snippet["description"]
        published = parse_date(snippet["publishedAt"])
        if published:
            item.published = datetime.fromtimestamp(mktime(published))
        item.thumbnail = snippet["thumbnails"]["high"]["url"]

        yield item


@final
class YoutubeSpider(Spider):
    def __init__(self, channels: list[tuple[str, Category]]):
        super().__init__(default_request_handler=default_handler)
        token = os.getenv("YOUTUBE_API_TOKEN")
        if not token:
            raise ValueError("YOUTUBE_API_TOKEN environment variable is not set")
        self.requests = [
            Request.from_url(
                url=f"https://youtube.googleapis.com/youtube/v3/search?part=snippet&channelId={cid}&maxResults=20&order=date&key={token}",
                user_data={"category": category},
            )
            for cid, category in channels
        ]

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(self.requests)
