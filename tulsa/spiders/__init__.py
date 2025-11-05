import importlib
import inspect
import logging
import os
import pkgutil
import tomllib
from typing import Literal, TypedDict

from crawlee import Request

from tulsa import HtmlSpider, Spider
from tulsa.models import Category

from .blogspot import BlogspotSpider
from .rss import RssProperties, RssSpider
from .spotify import SpotifySpider
from .youtube import YoutubeSpider


def load_spiders(
    folder: Literal["blog", "cve", "bounty_platform"],
) -> list[Spider | HtmlSpider]:
    """
    Automatically dynamic load all spiders in `folder`.
    """

    ret: list[Spider | HtmlSpider] = []
    for _, module_name, _ in pkgutil.iter_modules(
        [os.path.join(__path__[0], folder)],
        f"tulsa.spiders.{folder.replace('/', '.')}.",
    ):
        module = importlib.import_module(module_name)
        for class_name, class_obj in inspect.getmembers(module, inspect.isclass):
            if (
                (issubclass(class_obj, Spider) or issubclass(class_obj, HtmlSpider))
                and class_name != "Spider"
                and class_name != "HtmlSpider"
            ):
                try:
                    ret.append(class_obj())  # pyright: ignore [reportCallIssue]
                except Exception as e:
                    logging.getLogger(__name__).error(
                        f"Cannot load '{class_obj.__module__}.{class_name}' pipeline: {e}"
                    )

    return ret


def load_spiders_from_feeds(file_path: str = "feeds.toml") -> list[Spider | HtmlSpider]:
    class Feeds(TypedDict):
        rss: list[Request]
        blogspot: list[Request]
        youtube: list[tuple[str, Category]]
        spotify: list[tuple[str, Category]]

    rss_feeds: Feeds = {"rss": [], "blogspot": [], "youtube": [], "spotify": []}
    spiders: list[Spider | HtmlSpider] = []
    with open(file_path, "rb") as f:
        feeds = tomllib.load(f)
        for spider_name in feeds.keys():
            match spider_name:
                case "rss" | "blogspot":
                    for entry in feeds[spider_name]:
                        user_data: RssProperties = {
                            "only_tags": [],
                            "exclude_tags": [],
                            "in_urls": [],
                            "fix_link": [],
                            "category": Category.Generic,
                            "allow_empty": False,
                        }
                        user_data["only_tags"] = entry.get("only_tags")
                        user_data["exclude_tags"] = entry.get("exclude_tags")
                        user_data["in_urls"] = entry.get("in_urls")
                        user_data["fix_link"] = entry.get("fix_link")
                        user_data["category"] = entry.get("category", Category.Generic)
                        user_data["allow_empty"] = entry.get("allow_empty", False)
                        rss_feeds[spider_name].append(
                            Request.from_url(entry.get("url"), user_data=user_data)
                        )
                case "youtube" | "spotify":
                    for entry in feeds[spider_name]:
                        category = entry.get("category", Category.Generic)
                        rss_feeds[spider_name].append((entry.get("id"), category))
                case _:
                    logging.getLogger(__name__).warning(
                        f"Unknown spider's name: {spider_name}"
                    )
    if len(rss_feeds["blogspot"]) > 0:
        spiders.append(BlogspotSpider(rss_feeds["blogspot"]))
    if len(rss_feeds["rss"]) > 0:
        spiders.append(RssSpider(rss_feeds["rss"]))
    if len(rss_feeds["spotify"]) > 0:
        spiders.append(SpotifySpider(rss_feeds["spotify"]))
    if len(rss_feeds["youtube"]) > 0:
        spiders.append(YoutubeSpider(rss_feeds["youtube"]))

    return spiders


def get_spiders(
    types: list[Literal["blog", "cve"]],
) -> list[Spider | HtmlSpider]:
    result: list[Spider | HtmlSpider] = []
    for kind in set(types):
        match kind:
            case "blog":
                result += load_spiders_from_feeds()
                result += load_spiders("blog")
                result += load_spiders("bounty_platform")
            case "cve":
                result += load_spiders("cve")
    return result


__all__ = [
    "get_spiders",
    "BlogspotSpider",
    "RssSpider",
    "SpotifySpider",
    "YoutubeSpider",
]
