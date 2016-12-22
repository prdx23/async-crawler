import re
import sys
import json
import signal
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
FILENAME = 'graph.json'

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


async def worker(session, loop, sem):
    global count, cache, graph
    while True:
        depth, url, retries = await Q.get()
        if url == None:
            break
        if url in cache:
            continue

        try:
            async with sem:
                html_code = await get(session, url)
        except Exception as e:
            if retries + 1 <= MAX_RETRIES:
                Q.put_nowait((depth, url, retries + 1))
                continue
            else:
                print('[{}] ERROR : {}'.format(url, repr(e)))
        else:
            urls = extract_urls(html_code)
            count += 1
            cache.add(url)
            graph[url.split('wiki/')[1]] = [x.split('wiki/')[1] for x in urls]
            # print('Crawled : {}'.format(url))

            if depth + 1 <= MAX_DEPTH:
                for url in urls:
                    Q.put_nowait((depth + 1, url, retries))
            elif depth + 1 > MAX_DEPTH and Q.qsize() == 1:
                for _ in range(MAX_WORKERS):
                    Q.put_nowait((None, None, None))


async def main(loop):
    sem = asyncio.Semaphore(MAX_WORKERS)
    async with aiohttp.ClientSession(loop=loop) as session:
        workers = [worker(session, loop, sem) for x in range(MAX_WORKERS)]
        await asyncio.wait(workers)
    output_json()


def exit_early(signal, frame):
    output_json()
    sys.exit(0)


def output_json():
    with open(FILENAME, 'w') as fp:
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
    parser.add_argument(
        '-f', '--file', type=str,
        help='Filename to save the json in', default=None)

    args = parser.parse_args()
    MAX_DEPTH = args.depth if args.depth else MAX_DEPTH
    MAX_WORKERS = args.workers if args.workers else MAX_WORKERS
    MAX_RETRIES = args.retries if args.retries else MAX_RETRIES
    FILENAME = args.file if args.file else FILENAME
    start_url = args.url if args.url else '/wiki/Python_(programming_language)'

    signal.signal(signal.SIGINT, exit_early)
    print('Started crawling...')
    start = timer()
    Q.put_nowait((0, DOMAIN + start_url, 0))
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()
    end = timer()
    print('Time Taken for {} requests : {} sec'.format(count, end - start))

