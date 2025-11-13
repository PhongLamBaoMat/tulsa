from collections.abc import AsyncIterator, Callable
from typing import TypeVar, Unpack, final, override

from crawlee.crawlers import (
    BasicCrawlerOptions,
    BasicCrawlingContext,
    HttpCrawlingContext,
    ParselCrawler,
    ParselCrawlingContext,
)
from crawlee.errors import UserDefinedErrorHandlerError
from crawlee.http_clients import CurlImpersonateHttpClient
from crawlee.http_clients._curl_impersonate import (
    _AsyncSession,  # pyright: ignore [reportPrivateUsage]
)
from crawlee.router import RequestHandler, Router
from crawlee.storage_clients import MemoryStorageClient
from pydantic import BaseModel

from tulsa.pipelines import Pipeline, load_all_pipelines

type HtmlCrawlingContext = ParselCrawlingContext

TCrawlingContext = TypeVar("TCrawlingContext", HttpCrawlingContext, HtmlCrawlingContext)


@final
class SpiderRouter(Router[ParselCrawlingContext]):
    pipelines: list[Pipeline]

    def __init__(self) -> None:
        super().__init__()
        self.pipelines = sorted(
            filter(lambda p: p.enabled, load_all_pipelines()),
            key=lambda p: p.priority,
        )

    @override
    def default_handler(  # pyright: ignore [reportIncompatibleMethodOverride]
        self, handler: Callable[[ParselCrawlingContext], AsyncIterator[BaseModel]]
    ) -> RequestHandler[ParselCrawlingContext]:
        """Register a default request handler.

        The default request handler is invoked for requests that have either no label or a label for which we have
        no matching handler.
        """
        if self._default_handler is not None:
            raise RuntimeError("A default handler is already configured")

        async def wrapper(context: ParselCrawlingContext):
            async for item in handler(context):
                for pipeline in self.pipelines:
                    item = await pipeline.handle_item(item)
                    if not item:
                        break

                # Debug only
                # await context.push_data(item.model_dump())

        self._default_handler = wrapper

        return wrapper


class Spider(ParselCrawler):
    def __init__(
        self,
        *,
        default_request_handler: Callable[
            [HtmlCrawlingContext], AsyncIterator[BaseModel]
        ],
        allow_redirects: bool = True,
        **kwargs: Unpack[BasicCrawlerOptions[ParselCrawlingContext]],
    ) -> None:
        http_client = CurlImpersonateHttpClient()
        # We modify the default configuration to be able to disable TLS verification
        http_client._client_by_proxy_url[None] = _AsyncSession(  # pyright: ignore [reportPrivateUsage]
            **{
                "impersonate": "chrome",
                "verify": False,
                "allow_redirects": allow_redirects,
            }
        )
        # Workaround solution to disable the storage
        kwargs["storage_client"] = MemoryStorageClient()
        super().__init__(**kwargs)
        self.router = SpiderRouter()  # pyright: ignore [reportUnannotatedClassAttribute]
        _ = self.router.default_handler(default_request_handler)
        self.log.info(
            f"Loaded pipelines: {list(map(lambda x: f'{x.__class__.__module__}.{x.__class__.__name__}', self.router.pipelines))}"
        )

    @override
    async def _handle_failed_request(
        self, context: TCrawlingContext | BasicCrawlingContext, error: Exception
    ) -> None:
        await self._statistics.error_tracker.add(error=error, context=context)

        if self._failed_request_handler:
            try:
                await self._failed_request_handler(context, error)
            except Exception as e:
                raise UserDefinedErrorHandlerError(
                    "Exception thrown in user-defined failed request handler"
                ) from e
        else:
            self._logger.error(
                f"Request to {context.request.url} failed and reached maximum retries\n {self._get_message_from_error(error)}"
            )
