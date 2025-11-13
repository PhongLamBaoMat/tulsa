from collections.abc import AsyncIterator
from datetime import datetime
from time import mktime
from typing import TYPE_CHECKING, Any, TypedDict, cast, final, override
from urllib.parse import ParseResult as UrlParseResult
from urllib.parse import urljoin, urlparse

import feedparser
from bs4 import BeautifulSoup
from crawlee import Request
from crawlee.crawlers import ParselCrawlingContext
from crawlee.statistics import FinalStatistics

if TYPE_CHECKING:
    from feedparser.util import Item
else:
    type Item = Any

from tulsa import Spider
from tulsa.helpers import is_valid_url
from tulsa.models import Blog, Category


class RssProperties(TypedDict):
    only_tags: list[str]
    exclude_tags: list[str]
    in_urls: list[str]
    fix_link: list[str]
    category: Category
    allow_empty: bool


def __should_skip_by_path(path: str) -> bool:
    """Check if the URL path should be skipped."""
    return path.lower() in [
        "/blog",
        "/blogs",
        "/home",
        "/about",
        "/categories",
        "/post",
        "/posts",
        "/tag",
        "/tags",
        "/blog/",
        "/blogs/",
        "/home/",
        "/about/",
        "/categories/",
        "/post/",
        "/posts/",
        "/tag/",
        "/tags/",
        "/about.html",
    ]


def __do_have_tag(entry: Item, terms: list[str]) -> bool:
    """
    Return True if the entry has a tag in terms
    """
    found = False
    for tag in entry.get("tags") or []:
        if tag.get("term", "").lower() in terms:
            found = True
            break
    return found


def __check_tag_based_filters(
    entry: Item,
    required_terms: list[str] | None,
    skip_terms: list[str] | None,
) -> bool:
    """
    Check rss entry tag-based filtering rules.
    Return True if the entry isn't in any rules, or the entry is in `required_terms`
    Return False if the entry is in `skip_terms`
    """
    if skip_terms and len(skip_terms) > 0:
        # Skip the entry that has any of the tags in the skip_terms dictionary
        return not __do_have_tag(entry, skip_terms)
    elif required_terms and len(required_terms) > 0:
        # Take the entry that has any of the tags in the required_terms dictionary
        return __do_have_tag(entry, required_terms)
    return True


def __check_path_base_filters(
    parsed_url: UrlParseResult, required_paths: list[str] | None
) -> bool:
    """
    Check url path-based filtering rules.
    Only return True if the path matches the required paths.
    """
    if required_paths:
        for path in required_paths:
            if path in parsed_url.path:
                return True
        return False
    return True


def __fix_entry_link(entry_link: str, replacement: list[str] | None) -> str:
    if replacement:
        entry_link = entry_link.replace(replacement[0], replacement[1])

    return entry_link


def __process_entry_summary(entry: Item) -> str | None:
    """Process and extract the best summary from an entry."""
    summary = entry.get("description") or (
        entry["content"][0].value if entry.get("content") else None
    )
    if not summary:
        return None

    summary = cast(str, BeautifulSoup(summary, "lxml").text).strip()
    # Sometimes, the summary is very short, it isn't enough text
    # So we will use `entry.content` instead
    if entry.get("content"):
        new_summary = cast(
            str, BeautifulSoup(entry["content"][0].value, "lxml").text
        ).strip()
        if len(summary) < len(new_summary) and len(summary) < 20:
            summary = new_summary

    # Clean up multiple newlines
    summary = summary.strip()
    for _ in range(10):
        summary = summary.replace("\r\n", "\n")
        summary = summary.replace("\n\n\n", "\n\n")

    return summary[:1000]


def __extract_thumbnail(entry: Item) -> str | None:
    """
    Extract thumbnail URL from entry if available.
    """
    medias = entry.get("media_content") or entry.get("media_thumbnail")
    if medias:
        for m in medias:
            url = m.get("url")
            if url and "/avatar/" not in url and is_valid_url(url):
                return url
    else:
        for link in entry.get("links") or []:
            if (
                link.get("rel", "") == "enclosure"
                and (
                    link.get("type", "") == "image/png"
                    or link.get("type", "") == "image/jpeg"
                )
                and link.get("href")
                and is_valid_url(link["href"])
            ):
                return link["href"]
    return None


# TODO: Implement category extraction logic while parsing feeds.toml
def __extract_category(rss_url: str, entry: Item) -> Category | None:
    """
    Extract entry's category from the entry's tags/categories if avaiable
    """
    # The key is rss url, the value is a tuple contains 2 elements
    # The first element is a tag array
    # that indicate the category type corresponds to the second element
    sites = {"https://medium.com/feed/@numencyberlabs": (["web3"], Category.Blockchain)}
    if rss_url in sites:
        if __do_have_tag(entry, sites[rss_url][0]):
            return sites[rss_url][1]
    return None


async def default_handler(context: ParselCrawlingContext) -> AsyncIterator[Blog]:
    entries = feedparser.parse(await context.http_response.read()).entries
    user_data = cast(RssProperties, context.request.user_data)  # pyright: ignore [reportInvalidCast]

    if len(entries) == 0 and not user_data.get("allow_empty"):
        context.log.error(f"'{context.request.url}' doesn't have any entries to read")
        return

    for entry in entries:
        if not entry.get("link") or not entry.get("title"):
            continue

        link = entry["link"]
        title = entry["title"]
        parsed_link = urlparse(link)
        if __should_skip_by_path(parsed_link.path):
            continue
        if not __check_path_base_filters(parsed_link, user_data.get("in_urls")):
            continue
        if not __check_tag_based_filters(
            entry, user_data.get("only_tags"), user_data.get("exclude_tags")
        ):
            continue
        url = __fix_entry_link(link, user_data.get("fix_link"))
        category = __extract_category(url, entry) or user_data.get(
            "category", Category.Generic
        )

        data = Blog(
            url=urljoin(context.request.loaded_url or context.request.url, url),
            title=title,
            category=category,
        )
        if entry.get("author"):
            data.author = entry["author"]
        summary = __process_entry_summary(entry)
        if summary:
            data.description = summary
        published_parsed = entry.get("published_parsed") or entry.get("updated_parsed")
        if published_parsed:
            # It's weird when we collect an item what is published before 1975
            if published_parsed.tm_year <= 1975:
                continue
            data.published = datetime.fromtimestamp(mktime(published_parsed))
        thumbnail = __extract_thumbnail(entry)
        if thumbnail:
            data.thumbnail = thumbnail

        yield data


@final
class RssSpider(Spider):
    def __init__(self, requests: list[Request]):
        super().__init__(default_request_handler=default_handler)
        self.requests = requests

    @override
    async def run(self) -> FinalStatistics:  # pyright: ignore [reportIncompatibleMethodOverride]
        return await super().run(self.requests)
