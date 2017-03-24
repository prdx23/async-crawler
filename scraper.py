import re
import asyncio
import async_timeout
from timeit import default_timer as timer

import aiohttp
from lxml import html
import motor.motor_asyncio
from pymongo import TEXT


class Crawler:

    client = motor.motor_asyncio.AsyncIOMotorClient()
    db = client.graph

    def __init__(self, *, domain, regexp, max_depth,
                 max_workers, max_retries, dbname):
        self.domain = domain
        self.max_depth = max_depth
        self.max_retries = max_retries
        self.max_workers = max_workers
        self.Q = asyncio.Queue()
        self.db_Q = asyncio.Queue()
        self.cache = set()
        self.count = 0
        self.regex = re.compile(regexp)
        self.loop = asyncio.get_event_loop()
        self.collection = self.db[dbname]
        self.collection.create_index([('p_url', TEXT)])

    async def get(self, url, timeout):
        with async_timeout.timeout(timeout):
            async with self.session.get(url) as response:
                return await response.text()

    async def extract_urls(self, url, timeout=10):
        tree = html.fromstring(await self.get(self.domain + url, timeout))
        urls_list = map(self.regex.findall, tree.xpath('//a/@href'))
        return {x[0] for x in urls_list if x != []}

    async def worker(self):
        while True:
            url, depth, retries, parent_url = await self.Q.get()
            if url in self.cache:
                print(f'Loaded from cache {url}')
                self.db_Q.put_nowait((parent_url, url))
                self.Q.task_done()
                continue
            try:
                new_urls = await self.extract_urls(url)
            except Exception as e:
                if retries <= self.max_retries:
                    print(f'Retrying {url}')
                    self.Q.put_nowait((url, depth, retries + 1, parent_url))
                else:
                    print(f'Error in {url}: {repr(e)}')
            else:
                self.cache.add(url)
                self.count += 1
                self.db_Q.put_nowait((parent_url, url))
                print(f'Depth [{depth}], Retry [{retries}]: Visited {url}')
                if depth+1 <= self.max_depth:
                    for x in new_urls:
                        self.Q.put_nowait((x, depth + 1, retries, url))
            self.Q.task_done()

    async def run(self):
        async with aiohttp.ClientSession(loop=self.loop) as session:
            self.session = session
            workers = (self.worker() for _ in range(self.max_workers))
            tasks = [self.loop.create_task(x) for x in workers]
            tasks += [self.loop.create_task(self.write_to_db())]
            await asyncio.sleep(5)
            await self.Q.join()
            await self.db_Q.join()
            for task in tasks:
                task.cancel()

    def start(self, start_url):
        self.Q.put_nowait((start_url, 0, 0, 'root'))
        self.start_time = timer()
        self.loop.run_until_complete(asyncio.gather(self.run()))
        self.loop.close()
        print(f"Crawler for {self.domain} Finished !")
        print(f"It took {timer() - self.start_time} secs "
              f"to complete {self.count} requests")

    async def write_to_db(self):
        while True:
            p_url, c_url = await self.db_Q.get()
            await self.collection.find_one_and_update(
                {'$text': {'$search': p_url}, 'c_url': c_url}, {
                    '$inc': {'count': 1},
                    '$setOnInsert': {'p_url': p_url, 'c_url': c_url},
                }, upsert=True)
            self.db_Q.task_done()


if __name__ == '__main__':
    url = '/wiki/Python_(programming_language)'
    options = {
        'domain': 'https://en.wikipedia.org',
        'regexp': r"^(\/wiki\/[^:#\s]+)(?:$|#)",
        'max_depth': 1,
        'max_workers': 30,
        'max_retries': 5,
        'dbname': 'test2',
    }
    c = Crawler(**options)
    c.start(url)
