import re
import asyncio
import async_timeout

import aiohttp
from lxml import html

DOMAIN = 'https://en.wikipedia.org'
REGEX = re.compile(r"^(\/wiki\/[^:#\s]+)(?:$|#)")
Q = asyncio.Queue()
MAX_DEPTH = 1
MAX_WORKERS = 20

async def get(session, url, timeout=10):
    with async_timeout.timeout(timeout):
        async with session.get(url) as response:
            return await response.text()


def extract_urls(html_code):
    tree = html.fromstring(html_code)
    urls_list = map(REGEX.findall, tree.xpath('//a/@href'))
    return {DOMAIN + x[0] for x in urls_list if x != []}


async def worker(loop):
    async with aiohttp.ClientSession(loop=loop) as session:
        while True:
            depth, url = await Q.get()
            if url == None:
                break

            print('Request sent for {}'.format(url))
            urls = extract_urls(await get(session, url))
            print('Done : {}'.format(url))

            if depth + 1 > MAX_DEPTH:
                for _ in range(MAX_WORKERS):
                    Q.put_nowait((None, None))
            else:
                for url in urls:
                    Q.put_nowait((depth + 1, url))


def main():
    Q.put_nowait((0, DOMAIN + '/wiki/Python_(programming_language)'))
    loop = asyncio.get_event_loop()
    workers = [worker(loop) for x in range(MAX_WORKERS)]
    loop.run_until_complete(asyncio.wait(workers))
    loop.close()


if __name__ == '__main__':
    main()
