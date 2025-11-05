import logging
import os
from typing import Any, cast, override

from pydantic import BaseModel
from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection

from tulsa.models import Blog, Cve, HacktivityBounty
from tulsa.pipelines import Pipeline


class Mongodb(Pipeline):
    logger: logging.Logger

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        url = os.getenv("MONGODB_URL")
        if not url:
            raise ValueError("MONGODB_URL environment variable is not set")
        self.__client: AsyncMongoClient[Any] = AsyncMongoClient(url)
        self.__db = self.__client.get_database("tulsa")

    @property
    @override
    def enabled(self) -> bool:
        return True

    @property
    @override
    def priority(self) -> int:
        return 9999

    async def handle_blog(self, blog: Blog):
        collection: AsyncCollection[Any] = self.__db["blog"]

        async with self.__client.start_session() as session:
            async with await session.start_transaction():
                if not await collection.find_one({"url": blog.url}):
                    _ = await collection.insert_one(blog.model_dump())

    async def handle_hacktivity_bounty(self, item: HacktivityBounty):
        collection: AsyncCollection[Any] = self.__db["blog"]

        async with self.__client.start_session() as session:
            async with await session.start_transaction():
                if not await collection.find_one({"url": item.url}):
                    _ = await collection.insert_one(item.model_dump())

    async def handle_cve(self, cve: Cve):
        collection: AsyncCollection[Any] = self.__db["cve"]

        async with self.__client.start_session() as session:
            async with await session.start_transaction():
                result = await collection.find_one({"id": cve.id})

                if not result:
                    _ = await collection.insert_one(cve.model_dump())
                else:
                    current_cve = Cve.model_validate(result)
                    # The cve is collected from different sources
                    # but some of sources don't have enough CVE information
                    # we do this to fullfill the missing fields
                    # The first source is always NIST
                    # then the 2nd, 3rd,... source will fill the remain fields
                    if (
                        current_cve.score == 0
                        and not current_cve.sent
                        and cve.score > 0
                    ):
                        _ = await collection.update_one(
                            {"id": current_cve.id}, {"$set": {"score": cve.score}}
                        )
                    current_description: str = (
                        current_cve.description
                        if current_cve.description is not None
                        else ""
                    )
                    description = cve.description if cve.description is not None else ""
                    # We would prefer the shorter description
                    # NIST is ofter better at this
                    if (
                        len(description) < len(current_description)
                        and len(description) > 0
                        and current_cve.sent is False
                    ):
                        _ = await collection.update_one(
                            {"id": current_cve.id},
                            {"$set": {"description": description}},
                        )

    @override
    async def handle_item(self, item: BaseModel) -> BaseModel | None:
        if item.__class__ is Blog:
            await self.handle_blog(cast(Blog, item))
        elif item.__class__ is HacktivityBounty:
            await self.handle_hacktivity_bounty(cast(HacktivityBounty, item))
        elif item.__class__ is Cve:
            await self.handle_cve(cast(Cve, item))
        else:
            self.logger.error(f"Doesn't support item type: {item.__class__}")

        return item
