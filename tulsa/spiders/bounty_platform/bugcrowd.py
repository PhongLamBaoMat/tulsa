import json
import os
from collections.abc import AsyncIterator
from datetime import datetime
from time import mktime
from typing import TypedDict, cast, final, override
from urllib.parse import urlencode

from crawlee import Request
from crawlee.crawlers import (
    HttpCrawlingContext,
)
from crawlee.statistics import FinalStatistics
from pyotp import TOTP

from tulsa import Spider
from tulsa.helpers import parse_date
from tulsa.models import HacktivityBounty


class BugcrowdAuth(TypedDict):
    username: str
    password: str
    totp_token: str


async def default_request_handler(
    context: HttpCrawlingContext,
) -> AsyncIterator[HacktivityBounty]:
    res = json.loads(await context.http_response.read())
    for entry in res.get("results", []):
        url = f"https://bugcrowd.com{entry['disclosure_report_url']}"
        title = entry["title"]
        published = parse_date(entry["disclosed_at"])
        reporter = entry["researcher_username"]
        program = entry["engagement_name"]
        awarded = (
            float(entry["amount"].lstrip("$").replace(",", ""))
            if entry.get("amount")
            else None
        )

        match entry["priority"]:
            case 5:
                severity = "information"
            case 4:
                severity = "low"
            case 3:
                severity = "medium"
            case 2:
                severity = "high"
            case 1:
                severity = "critial"
            case _:
                severity = None

        item = HacktivityBounty(url=url, title=title)
        if published:
            item.published = datetime.fromtimestamp(mktime(published))
        item.reporter = reporter
        item.program = program
        item.awarded = awarded
        item.severity = severity  # pyright: ignore [reportAttributeAccessIssue]
        yield item


async def login(context: HttpCrawlingContext):
    if context.session is None:
        context.log.error("The request session is None")
        return

    user_data = cast(BugcrowdAuth, context.request.user_data)  # pyright: ignore [reportInvalidCast]

    await context.add_requests(
        [
            Request.from_url(
                "https://identity.bugcrowd.com/login",
                method="POST",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-Csrf-Token": context.session.cookies["csrf-token"],  # pyright: ignore [reportArgumentType]
                    "Origin": "https://identity.bugcrowd.com",
                },
                payload=urlencode(
                    {
                        "username": user_data["username"],
                        "password": user_data["password"],
                        "otp_code": "",
                        "backup_otp_code": "",
                        "user_type": "RESEARCHER",
                        "remember_me": "false",
                    }
                ),
                label="otp_challenge",
                user_data=user_data,
                session_id=context.session.id,
            )
        ]
    )


async def otp_challenge(context: HttpCrawlingContext):
    if context.session is None:
        context.log.error("The request session is None")
        return

    user_data = cast(BugcrowdAuth, context.request.user_data)  # pyright: ignore [reportInvalidCast]

    await context.add_requests(
        [
            Request.from_url(
                "https://identity.bugcrowd.com/auth/otp-challenge",
                method="POST",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-Csrf-Token": context.session.cookies["csrf-token"],  # pyright: ignore [reportArgumentType]
                    "Origin": "https://identity.bugcrowd.com",
                },
                payload=urlencode(
                    {
                        "username": user_data["username"],
                        "password": user_data["password"],
                        "otp_code": TOTP(user_data["totp_token"]).now(),
                        "backup_otp_code": "",
                        "user_type": "RESEARCHER",
                        "remember_me": "false",
                    }
                ),
                label="set_session",
                session_id=context.session.id,
            )
        ]
    )


async def set_session(context: HttpCrawlingContext):
    if context.session is None:
        context.log.error("The request session is None")
        return

    await context.add_requests(
        [
            Request.from_url(
                f"https://bugcrowd.com/crowdstream.json?page={i}&filter_by=disclosures",
                session_id=context.session.id,
            )
            for i in range(1, 4)
        ]
    )


@final
class BugcrowdHacktivitySpider(Spider):
    def __init__(self):
        super().__init__(
            default_request_handler=default_request_handler,
            ignore_http_error_status_codes=[422],
        )
        self.router._handlers_by_label["login"] = login  # pyright: ignore [reportPrivateUsage]
        self.router._handlers_by_label["otp_challenge"] = otp_challenge  # pyright: ignore [reportPrivateUsage]
        self.router._handlers_by_label["set_session"] = set_session  # pyright: ignore [reportPrivateUsage]

        auth = os.getenv("BUGCROWD_AUTH")
        if not auth:
            raise ValueError("BUGCROWD_AUTH environment variable is not set")
        self.username, self.password, self.topt_token = auth.split("|")

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(
            [
                Request.from_url(
                    "https://identity.bugcrowd.com/login?user_hint=researcher",
                    label="login",
                    user_data={
                        "username": self.username,
                        "password": self.password,
                        "totp_token": self.topt_token,
                    },
                )
            ]
        )
