import asyncio
from crawl4ai import AsyncWebCrawler
from bs4 import BeautifulSoup

async def main(url: str) -> str:
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url=url
        )

        html = result.html  
        soup = BeautifulSoup(html, "lxml")

        title = soup.title.text if soup.title else None

        author = soup.find("meta", {"name": "author"})
        author = author["content"] if author else None

        description = soup.find("meta", {"name": "description"})
        description = description["content"] if description else None

        # Use crawl4ai's built-in markdown extraction for full content,
        # instead of relying on the <article> tag which is incomplete on this page.
        content = result.markdown

        data = {
            "title": title,
            "author": author,
            "description": description,
            "content": content,
            "url": result.url
        }
        print("**************************************")
        print(data)
        print("******************************************")
        print(f'data length: {len(data)}')
        print(f'title length: {len(data["title"])}')
        #print(f'author length: {len(data["author"])}')
        #print(f'description length: {len(data["description"])}')
        print(f'content length: {len(data["content"])}')
        print("******************************************")
    return content
# asyncio.run(main())
