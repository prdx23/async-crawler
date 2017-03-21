import re
import asyncio
import async_timeout

import aiohttp
from lxml import html


class Crawler:

    def __init__(self, *, domain, regexp, max_depth, max_workers):
        self.domain = domain
        self.regex = re.compile(regexp)
        self.max_depth = max_depth
        self.max_workers = max_workers
        self.Q = asyncio.Queue()
        self.cache = set()
        self.count = 0
        self.loop = asyncio.get_event_loop()

    async def get(self, url, timeout=10):
        with async_timeout.timeout(timeout):
            async with self.session.get(url) as response:
                return await response.text()


    async def extract_urls(self, url):
        tree = html.fromstring(await self.get(url))
        urls_list = map(self.regex.findall, tree.xpath('//a/@href'))
        return {self.domain + x[0] for x in urls_list if x != []}


    async def worker(self):
        while True:
            url, depth = await self.Q.get()
            #  print(f'starting {url}')
            new_urls = await self.extract_urls(url)
            self.Q.task_done()
            print(f'At depth {depth}: Downloaded {url}')
            for url in new_urls:
                if depth+1 <= self.max_depth:
                    self.Q.put_nowait((url, depth + 1))

    async def run(self):
        async with aiohttp.ClientSession(loop=self.loop) as session:
            self.session = session
            workers = [self.worker() for _ in range(self.max_workers)]

            for w in workers:
                asyncio.ensure_future(w)

            await asyncio.sleep(3)
            await self.Q.join()
            for w in workers:
                w.cancel()
            self.loop.close()

    def start(self, start_url):
        self.Q.put_nowait((start_url, 0))
        self.loop.run_until_complete(asyncio.gather(self.run()))


if __name__ == '__main__':
    url = 'https://en.wikipedia.org/wiki/Python_(programming_language)'
    options = {
        'domain': 'https://en.wikipedia.org',
        'regexp': r"^(\/wiki\/[^:#\s]+)(?:$|#)",
        'max_depth': 1,
        'max_workers': 100,
    }
    c = Crawler(**options)
    c.start(url)
