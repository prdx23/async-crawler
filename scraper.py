import re
import json
import asyncio
import argparse
import async_timeout
from timeit import default_timer as timer

import aiohttp
from lxml import html

DOMAIN = 'https://en.wikipedia.org'
REGEX = re.compile(r"^(\/wiki\/[^:#\s]+)(?:$|#)")
Q = asyncio.Queue()

MAX_DEPTH = 1
MAX_RETRIES = 5
MAX_WORKERS = 20

count = 0
cache = set()
graph = {}

async def get(session, url, timeout=10):
    with async_timeout.timeout(timeout):
        async with session.get(url) as response:
            return await response.text()


def extract_urls(html_code):
    tree = html.fromstring(html_code)
    urls_list = map(REGEX.findall, tree.xpath('//a/@href'))
    return {DOMAIN + x[0] for x in urls_list if x != []}


async def worker(loop):
    global count, cache, graph
    async with aiohttp.ClientSession(loop=loop) as session:
        while True:
            depth, url, retries = await Q.get()
            if url == None:
                break
            if url in cache:
                continue

            try:
                html_code = await get(session, url)
            except asyncio.TimeoutError:
                if retries + 1 <= MAX_RETRIES:
                    Q.put_nowait((depth, url, retries + 1))
                    continue

            urls = extract_urls(html_code)
            count += 1
            cache.add(url)
            graph[url.split('wiki/')[1]] = [x.split('wiki/')[1] for x in urls]
            print('Crawled : {}'.format(url))

            if depth + 1 <= MAX_DEPTH:
                for url in urls:
                    Q.put_nowait((depth + 1, url, retries))
            elif depth + 1 > MAX_DEPTH and Q.qsize() == 1:
                for _ in range(MAX_WORKERS):
                    Q.put_nowait((None, None, None))


def main(start_url):
    Q.put_nowait((0, DOMAIN + start_url, 0))
    loop = asyncio.get_event_loop()
    workers = [worker(loop) for x in range(MAX_WORKERS)]
    loop.run_until_complete(asyncio.wait(workers))
    loop.close()
    output_json()


def output_json():
    with open('graph.json', 'w') as fp:
        json.dump(graph, fp)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='A recursive wikipidia crawler which creates a graph of '
        'connected pages')
    parser.add_argument(
        '-d', '--depth', type=int,
        help='Max recursion depth (default=1)', default=None)
    parser.add_argument(
        '-w', '--workers', type=int,
        help='Max concurrent Workers (default=1)', default=None)
    parser.add_argument(
        '-r', '--retries', type=int,
        help='Max no of retries for timeout errors (default=1)', default=None)
    parser.add_argument(
        '-u', '--url', type=str,
        help='Starting url', default=None)

    args = parser.parse_args()
    MAX_DEPTH = args.depth if args.depth else MAX_DEPTH
    MAX_WORKERS = args.workers if args.workers else MAX_WORKERS
    MAX_RETRIES = args.retries if args.retries else MAX_RETRIES
    start_url = args.url if args.url else '/wiki/Python_(programming_language)'

    print('Started crawling...')
    start = timer()
    main(start_url)
    end = timer()
    print('Time Taken for {} requests : {} sec'.format(count, end - start))
