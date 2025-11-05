import re
import time
from urllib.parse import parse_qs, urlencode, urlparse

import feedparser
from feedparser.datetimes import (
    _parse_date as parse_date,  # pyright: ignore [reportPrivateUsage]
)


def is_valid_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return all([parsed.scheme, parsed.netloc])
    except Exception:
        return False


def remove_url_query(url: str) -> str:
    """
    Remove some "source" parameters from the URL.

    Such as some blogs are from medium.com
    """
    url_parsed = urlparse(url)
    queries = parse_qs(url_parsed.query)
    sources = queries.get("utm_source", [])
    for source in sources:
        if source.startswith("rss"):
            del queries["utm_source"]
            break
    sources = queries.get("utm_medium", [])
    for source in sources:
        if source.startswith("rss"):
            del queries["utm_medium"]
            break
    sources = queries.get("source", [])
    for source in sources:
        if source.startswith("rss"):
            del queries["source"]
            break
    if queries.get("utm_campaign"):
        del queries["utm_campaign"]
    url = url_parsed._replace(query=urlencode(queries, doseq=True)).geturl()
    return url


def parse_date_MDY(date_str: str) -> time.struct_time | None:
    """
    Parses a date string in the format `Month Day, Year` and returns a tuple of integers (month, day, year).
    Returns None if the date string is not in the correct format.

    This function is different from `parse_date_mDY` because this function expects the Month name to be spelled out in full.
    """
    month_dict = {
        "January": 1,
        "February": 2,
        "March": 3,
        "April": 4,
        "May": 5,
        "June": 6,
        "July": 7,
        "August": 8,
        "September": 9,
        "October": 10,
        "November": 11,
        "December": 12,
    }
    match = re.match(r"(\w+) (\d{1,2}), (\d{4})", date_str)
    if match is None or month_dict.get(match.group(1)) is None:
        return None
    return parse_date(f"{match.group(3)}-{month_dict[match.group(1)]}-{match.group(2)}")


def parse_date_mDY(date_str: str) -> time.struct_time | None:
    """
    Parses a date string in the format `Mon Day, Year` and returns a tuple of integers (month, day, year).
    Returns None if the date string is not in the correct format.

    This function is different from `parse_date_MDY` because this function expects the Month name to be spelled out in short form.
    """
    month_dict = {
        "Jan": 1,
        "Feb": 2,
        "Mar": 3,
        "Apr": 4,
        "May": 5,
        "Jun": 6,
        "Jul": 7,
        "Aug": 8,
        "Sep": 9,
        "Oct": 10,
        "Nov": 11,
        "Dec": 12,
    }
    match = re.match(r"(\w{3}) (\d{1,2}), (\d{4})", date_str)
    if match is None or month_dict.get(match.group(1)) is None:
        return None
    return parse_date(f"{match.group(3)}-{month_dict[match.group(1)]}-{match.group(2)}")


feedparser.registerDateHandler(parse_date_MDY)
feedparser.registerDateHandler(parse_date_mDY)


__all__ = ["is_valid_url", "parse_date", "remove_url_query"]
