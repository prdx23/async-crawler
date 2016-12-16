import asyncio


async def test(a):
    print('started {}'.format(a))
    await asyncio.sleep(2)
    print('finish {}'.format(a))


def main():
    coroutines = [test(x) for x in range(10)]
    loop = asyncio.get_event_loop()
    c = asyncio.wait(coroutines)
    loop.run_until_complete(c)


if __name__ == '__main__':
    main()
