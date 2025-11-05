import asyncio
import logging
import os

import sentry_sdk
from apscheduler.events import (  # pyright: ignore [reportMissingTypeStubs]
    EVENT_JOB_ERROR,
    JobExecutionEvent,
)
from apscheduler.schedulers.asyncio import (  # pyright: ignore [reportMissingTypeStubs]
    AsyncIOScheduler,
)
from crawlee.crawlers import BasicCrawlingContext
from dotenv import load_dotenv
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.utils import event_from_exception

from tulsa.spiders import get_spiders

logger = logging.getLogger(__name__)


async def error_handler(context: BasicCrawlingContext, error: BaseException):
    event, hint = event_from_exception(error)
    event["message"] = f"{context.request.url} | {str(error)}"
    event["exception"]["values"][-1]["value"] = f"{context.request.url} | {str(error)}"  # pyright: ignore [reportTypedDictNotRequiredAccess]

    _ = sentry_sdk.capture_event(event, hint)


async def run_blog_spiders():
    for spider in get_spiders(["blog"]):
        _ = spider.failed_request_handler(error_handler)
        _ = spider.error_handler(error_handler)
        _ = await spider.run()


async def run_cve_spiders():
    for spider in get_spiders(["cve"]):
        _ = spider.failed_request_handler(error_handler)
        _ = spider.error_handler(error_handler)
        _ = await spider.run()


async def main() -> None:
    _ = load_dotenv()
    dsn = os.getenv("SENTRY_DSN")
    if dsn:
        _ = sentry_sdk.init(
            dsn=dsn,
            send_default_pii=False,
            integrations=[
                AsyncioIntegration(),
            ],
        )
    else:
        logger.warning("SENTRY_DSN environment variable isn't set")

    def sentry_listener(event: JobExecutionEvent):
        if event.exception:  # pyright: ignore [reportUnknownMemberType]
            _ = sentry_sdk.capture_exception(event.exception)  # pyright: ignore [reportUnknownArgumentType, reportUnknownMemberType]

    scheduler = AsyncIOScheduler()
    _ = scheduler.add_job(run_blog_spiders, "cron", hour="7,19", minute=30)  # pyright: ignore [reportUnknownMemberType]
    _ = scheduler.add_job(run_cve_spiders, "cron", minute=20)  # pyright: ignore [reportUnknownMemberType]
    _ = scheduler.add_listener(sentry_listener, EVENT_JOB_ERROR)  # pyright: ignore [reportUnknownMemberType]

    scheduler.start()

    while True:
        await asyncio.sleep(1)
