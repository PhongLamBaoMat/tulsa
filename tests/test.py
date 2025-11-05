import asyncio
import sys

sys.path.append("..")

from tulsa.spiders.blog.coinspect_com import CoinspectComSpider


async def main():
    crawler = CoinspectComSpider()
    _ = await crawler.run()
    pass


if __name__ == "__main__":
    asyncio.run(main())
