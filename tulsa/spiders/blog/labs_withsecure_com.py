import json
from datetime import datetime
from typing import cast, override
from urllib.parse import urljoin

from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.models import Blog


class LabsWithsecureComSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                "https://labs.withsecure.com/publications/_jcr_content/root/responsivegrid/responsivegrid/responsivegrid/customcontainer_copy/custom-container/customcontainer/custom-container/pagefilter.model.json"
            ]
        )

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        items = json.loads(await context.http_response.read()).get("items", [])

        if len(items) == 0:
            context.log.error(f"{context.request.url} | JSON response is empty")
            return

        for entry in items[:20]:
            title = entry.get("title")
            if not title:
                context.log.error(f"{context.request.url} | Entry doesn't have title")
                continue
            url = entry.get("pageUrl")
            if not url:
                context.log.error(f"{context.request.url} | Entry doesn't have url")
                continue
            published = entry.get("orderDate")
            description = cast(str | None, entry.get("description"))
            thumbnail = entry.get("imagePath")

            item = Blog(url=url, title=title)
            if description:
                item.description = description.removeprefix(
                    "\u003cp\u003e"
                ).removesuffix("\u003c/p\u003e\r\n")
            if thumbnail:
                item.thumbnail = urljoin(
                    context.request.loaded_url or context.request.url, thumbnail
                )
            if published:
                item.published = datetime.fromtimestamp(int(published) / 1000)

            yield item
