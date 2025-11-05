import logging
import re
from datetime import UTC, datetime
from typing import cast, override

from pydantic import BaseModel

from tulsa.helpers import remove_url_query
from tulsa.models import Blog, HacktivityBounty
from tulsa.pipelines import Pipeline


class DescriptionFilter(Pipeline):
    logger: logging.Logger

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        # Optimize regex compilation, not sure it's necessary!
        self.__re1 = re.compile(
            r"^The post .+ (first|appeared) on .+$", flags=re.M | re.I
        )
        self.__re2 = re.compile(r"… .+Read More »$", flags=re.M | re.I)
        self.__re3 = re.compile(r"^Read More ».+", flags=re.M | re.I)
        self.__re4 = re.compile(r"Continue reading on .+$", flags=re.M | re.I)

    @property
    @override
    def enabled(self) -> bool:
        return True

    @property
    @override
    def priority(self) -> int:
        return 1

    @override
    async def handle_item(self, item: BaseModel) -> BaseModel | None:
        if item.__class__ is Blog:
            item = cast(Blog, item)
            if item.description and len(item.description) > 0:
                item.description = self.__re1.sub("", item.description)
                item.description = self.__re2.sub("… ", item.description)
                item.description = self.__re3.sub("", item.description)
                item.description = self.__re4.sub("", item.description)
        # else:
        #     self.logger.warning(f"Unsupport item type: {item.__class__}")
        #     pass
        return item


class UrlDeduplication(Pipeline):
    @property
    @override
    def enabled(self) -> bool:
        return True

    @property
    @override
    def priority(self) -> int:
        return 1

    @override
    async def handle_item(self, item: BaseModel) -> BaseModel | None:
        if item.__class__ is Blog or item.__class__ is HacktivityBounty:
            url = cast(str, item.__getattribute__("url"))
            url = url.rstrip("/")
            url = remove_url_query(url)
            item.__setattr__("url", url)

        return item


class OutOfDateItem(Pipeline):
    """
    We don't collect items which are older then 7 days.
    """

    @property
    @override
    def enabled(self) -> bool:
        return True

    @property
    @override
    def priority(self) -> int:
        return 0

    @override
    async def handle_item(self, item: BaseModel) -> BaseModel | None:
        if item.__class__ is Blog or item.__class__ is HacktivityBounty:
            published = cast(datetime | None, item.__getattribute__("published"))
            if published:
                if (
                    datetime.now(UTC).timestamp() - published.timestamp()
                    > 60 * 60 * 24 * 7
                ):
                    return None
        return item
