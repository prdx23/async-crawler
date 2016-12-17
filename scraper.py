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


def extract_urls(html_code):
    tree = html.fromstring(html_code)
    urls_list = map(REGEX.findall, tree.xpath('//a/@href'))
    return {DOMAIN + x[0] for x in urls_list if x != []}


async def test(loop):
    url = 'https://en.wikipedia.org/wiki/Python_(programming_language)'
    async with aiohttp.ClientSession(loop=loop) as session:
        print('Request sent for {}'.format(url))
        html_code = await get(session, url)
        print('html recieved')
        urls = extract_urls(html_code)
        return urls


def main():
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(test(loop))
    for i, u in enumerate(res):
        print(i, u)
    print(len(res))


if __name__ == '__main__':
    main()
