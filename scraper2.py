import re
import asyncio
import async_timeout

import aiohttp
from lxml import html

DOMAIN = 'https://en.wikipedia.org'
REGEX = re.compile(r"^(\/wiki\/[^:#\s]+)(?:$|#)")


async def get(session, url, timeout=10):
    with async_timeout.timeout(timeout):
        async with session.get(url) as response:
            return await response.text()


async def extract_urls(url, session, current_depth=0):
    print(f'starting {url}')
    tree = html.fromstring(await get(session, url))
    urls_list = map(REGEX.findall, tree.xpath('//a/@href'))
    print(f'Downloaded {url}')


    return {DOMAIN + x[0] for x in urls_list if x != []}


async def scheduler():
    async with aiohttp.ClientSession(loop=loop) as session:
        pass


async def main(loop):
    url = DOMAIN + '/wiki/Python_(programming_language)'
    async with aiohttp.ClientSession(loop=loop) as session:
        await extract_urls(url, session)

loop = asyncio.get_event_loop()
loop.run_until_complete(main(loop))
loop.close()
