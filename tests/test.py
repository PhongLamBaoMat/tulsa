import asyncio

from dotenv import load_dotenv

from tulsa.spiders.blog.issues_chromium_org import ProjectZeroIssueTracker


async def main():
    crawler = ProjectZeroIssueTracker()
    _ = await crawler.run()


if __name__ == "__main__":
    _ = load_dotenv()
    asyncio.run(main())
