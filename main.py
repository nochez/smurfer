import asyncio
import itertools
import sys
import json
import pprint
from aiohttp import ClientSession


spinner = itertools.cycle(['-', '/', '|', '\\'])
async def spinner_wait():
    while True:
        sys.stdout.write(next(spinner))
        sys.stdout.flush()
        sys.stdout.write('\b')
        await asyncio.sleep(0.1)


base_url = 'https://aoe2.net/api'

async def get_user(user):
    endpoint = '/leaderboard'
    parameters = {'game':'aoe2de', 'leaderboard_id':'4', 'count':'1', 'search':user}
    async with ClientSession() as session:
        async with session.get(base_url+endpoint, params=parameters) as response:
            response = await response.read()
            user_data = json.loads(response)
            return user_data


async def get_last_match():
    endpoint = '/strings'
    parameters = {'game':'aoe2de', 'search':user}
    async with ClientSession() as session:
        async with session.get(base_url+endpoint) as response:
            response = await response.read()
            print(response)


async def main():
    user = input("User: ")
    tasks = []
    tasks.append(asyncio.ensure_future(get_user(user)))
    # We display while we wait
    spinner = asyncio.ensure_future(spinner_wait())
    await asyncio.gather(*tasks)
    # Got what we wanted so stop waiting
    spinner.cancel()


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()

