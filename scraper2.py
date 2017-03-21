import re
import asyncio
import async_timeout

import aiohttp
from lxml import html


class Crawler:

    def __init__(self, *, domain, regexp, max_depth, max_workers, max_retries):
        self.domain = domain
        self.regex = re.compile(regexp)
        self.max_depth = max_depth
        self.max_retries = max_retries
        self.max_workers = max_workers
        self.Q = asyncio.Queue()
        self.cache = set()
        self.count = 0
        self.loop = asyncio.get_event_loop()


    async def get(self, url, timeout):
        with async_timeout.timeout(timeout):
            async with self.session.get(url) as response:
                return await response.text()


    async def extract_urls(self, url, timeout=10):
        tree = html.fromstring(await self.get(url, timeout))
        urls_list = map(self.regex.findall, tree.xpath('//a/@href'))
        return {self.domain + x[0] for x in urls_list if x != []}


    async def worker(self):
        while True:
            url, depth, retries = await self.Q.get()
            if url in self.cache:
                print(f'Loaded from cache {url}')
                self.Q.task_done()
                continue
            try:
                new_urls = await self.extract_urls(url)
            except Exception as e:
                if retries <= self.max_retries:
                    print(f'Retrying {url}')
                    self.Q.put_nowait((url, depth, retries + 1))
                else:
                    print(f'Error in {url}: {repr(e)}')
            else:
                self.cache.add(url)
                self.count += 1
                print(f'Depth [{depth}], Retry [{retries}]: Downloaded {url}')
                for url in new_urls:
                    if depth+1 <= self.max_depth:
                        self.Q.put_nowait((url, depth + 1, retries))
            self.Q.task_done()


    async def run(self):
        async with aiohttp.ClientSession(loop=self.loop) as session:
            self.session = session
            workers = (self.worker() for _ in range(self.max_workers))
            tasks = [self.loop.create_task(x) for x in workers]
            await asyncio.sleep(5)
            await self.Q.join()
            for task in tasks:
                task.cancel()


    def start(self, start_url):
        self.Q.put_nowait((start_url, 0, 0))
        self.loop.run_until_complete(asyncio.gather(self.run()))
        self.loop.close()


if __name__ == '__main__':
    url = 'https://en.wikipedia.org/wiki/Python_(programming_language)'
    options = {
        'domain': 'https://en.wikipedia.org',
        'regexp': r"^(\/wiki\/[^:#\s]+)(?:$|#)",
        'max_depth': 1,
        'max_workers': 30,
        'max_retries': 5,
    }
    c = Crawler(**options)
    c.start(url)
