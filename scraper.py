import re
import asyncio

import aiohttp
from lxml import html

DOMAIN = 'https://en.wikipedia.org'
REGEX = re.compile(r"^(\/wiki\/[^:#\s]+)(?:$|#)")

async def get(url):
    r = await aiohttp.request('GET', url)
    html_code = await r.read()
    return html_code.decode("utf-8")


def extract_urls(html_code):
    tree = html.fromstring(html_code)
    urls_list = map(REGEX.findall, tree.xpath('//a/@href'))
    urls = {DOMAIN + x[0] for x in urls_list if x != []}
    return urls


async def test():
    url = 'https://en.wikipedia.org/wiki/Python_(programming_language)'
    print('Request sent for {}'.format(url))
    html_code = await get(url)
    print('html recieved')
    urls = extract_urls(html_code)
    return urls


def main():
    loop = asyncio.get_event_loop()
    coroutine = test()
    res = loop.run_until_complete(coroutine)
    for u in res:
        print(u)
    print(len(u))

if __name__ == '__main__':
    main()
