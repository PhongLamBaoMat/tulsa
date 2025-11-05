import json
import os
from collections.abc import AsyncIterator
from datetime import datetime
from time import mktime
from typing import TypedDict, cast, final, override
from urllib.parse import urlencode

from crawlee import Request
from crawlee.crawlers import HttpCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog, Category


class SpotifyProperties(TypedDict):
    category: Category


async def default_handler(context: HttpCrawlingContext) -> AsyncIterator[Blog]:
    res = json.loads(await context.http_response.read())
    user_data = cast(SpotifyProperties, context.request.user_data)  # pyright: ignore [reportInvalidCast]

    for entry in res["episodes"]["items"]:
        # Entry can be null
        if not entry:
            continue
        title = entry["name"]
        url = f"https://open.spotify.com/episode/{entry['id']}"
        category = user_data.get("category", Category.Generic)
        published = entry["release_date"]
        images = entry.get("images", [])
        description = entry["description"]

        item = Blog(url=url, title=title, category=category)
        item.author = entry["name"]
        published = parse_date(published)
        if published:
            item.published = datetime.fromtimestamp(mktime(published))
        item.description = description
        for image in images:
            item.thumbnail = image["url"]
            break

        yield item


async def fetch_access_token(context: HttpCrawlingContext):
    res = json.loads(await context.http_response.read())
    access_token = f"{res['token_type']} {res['access_token']}"
    context.request.user_data["access_token"] = access_token  # pyright: ignore [reportUnknownMemberType]


@final
class SpotifySpider(Spider):
    def __init__(self, shows: list[tuple[str, Category]]) -> None:
        super().__init__(default_request_handler=default_handler)
        self.router._handlers_by_label["fetch_access_token"] = fetch_access_token  # pyright: ignore [reportPrivateUsage]
        token = os.getenv("SPOTIFY_API_TOKEN")
        if not token:
            raise ValueError("SPOTIFY_API_TOKEN environment variable is not set")
        self.client_id, self.client_secret = token.split("|")
        self.shows = shows

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        # 1. Send a POST request to get access_token
        req = Request.from_url(
            "https://accounts.spotify.com/api/token",
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            payload=urlencode(
                {
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                }
            ),
            label="fetch_access_token",
        )
        _ = await super().run([req])
        access_token: str | None = req.user_data.get("access_token")  # pyright: ignore [reportAssignmentType, reportUnknownMemberType, reportUnknownVariableType]
        if not access_token:
            raise ValueError("Cannot get access token")

        # 2. Use access_token to get show's details
        requests = [
            Request.from_url(
                f"https://api.spotify.com/v1/shows/{show_id}",
                headers={"Authorization": access_token},
                user_data={"category": category},
            )
            for show_id, category in self.shows
        ]

        return await super().run(requests)
