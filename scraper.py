import re
import asyncio

import aiohttp
from lxml import html

async def get(url):
    r = await aiohttp.request('GET', url)
    html_code = await r.read()
    html_code = html_code.decode("utf-8")
    return html_code


def extract_urls(html_code):
    tree = html.fromstring(html_code)
    urls = tree.xpath('//a/@href')
    return urls


async def test():
    url = 'https://en.wikipedia.org/wiki/Python_(programming_language)'
    print('Request sent for {}'.format(url))
    html_code = await get(url)
    print(type(html_code))
    print('html recieved')
    urls = extract_urls(html_code)
    return urls


def main():
    loop = asyncio.get_event_loop()
    coroutine = test()
    res = loop.run_until_complete(coroutine)
    print(res)
    # urls = loop.run_until_complete(coroutine)
    # print(urls)

if __name__ == '__main__':
    main()
