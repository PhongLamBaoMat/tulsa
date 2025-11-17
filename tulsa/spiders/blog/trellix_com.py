import json
from datetime import datetime
from time import mktime
from typing import override
from urllib.parse import urljoin

from crawlee import Request
from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import Blog


class TrellixComSpider(Spider):
    def __init__(self) -> None:
        super().__init__(default_request_handler=self.default_request_handler)

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                Request.from_url(
                    "https://www.trellix.com/corpcomsvc/topicslisting?q=&newsPagePath=%2Fcontent%2Fmainsite%2Fen-us%2Fblogs%2Fresearch&_=1732419614544",
                ),
            ]
        )

    @staticmethod
    async def default_request_handler(context: ParselCrawlingContext):
        if (
            context.http_response.headers.get("Content-Type", "")
            == "application/json;charset=utf-8"
        ):
            items = json.loads(await context.http_response.read())["topics"]

            if len(items) == 0:
                context.log.error(f"{context.request.url} | Topics are empty")
                return

            for entry in items[:15]:
                title = entry["title"]
                url = urljoin(
                    context.request.loaded_url or context.request.url, entry["url"]
                )
                published = parse_date(entry["releaseDate"])
                description = entry["summary"]
                thumbnail = urljoin(
                    context.request.loaded_url or context.request.url,
                    entry["thumbnail"],
                )

                item = Blog(url=url, title=title)
                item.description = description
                item.thumbnail = thumbnail
                if published:
                    item.published = datetime.fromtimestamp(mktime(published))

                yield item
        else:
            meta_equiv = context.selector.xpath(
                '//meta[@http-equiv="refresh"]/@content'
            ).get()
            if not meta_equiv:
                context.log.error(
                    f"{context.request.url} | Cannot <meta http-equiv> tag"
                )
                return
            path = (
                "".join(meta_equiv.split(";")[1:])
                .strip()
                .removeprefix("URL='")
                .removesuffix("'")
            )
            if not context.session:
                context.log.error(
                    f"{context.request.url} | The request session is None"
                )
                return
            await context.add_requests(
                [
                    Request.from_url(
                        urljoin(
                            context.request.loaded_url or context.request.url, path
                        ),
                        session_id=context.session.id,
                    )
                ]
            )
