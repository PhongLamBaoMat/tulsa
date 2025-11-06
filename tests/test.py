import asyncio
import sys

from dotenv import load_dotenv

sys.path.append("..")

from tulsa.spiders.blog.medium_com import MediumComTagSpider


async def main():
    crawler = MediumComTagSpider()
    _ = await crawler.run()
    pass


if __name__ == "__main__":
    _ = load_dotenv()
    asyncio.run(main())
