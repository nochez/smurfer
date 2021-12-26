import asyncio
import itertools
import sys
import json
import pprint

from aiohttp import ClientSession
from types import SimpleNamespace

# Async spinner print
spinner = itertools.cycle(['-', '/', '|', '\\'])
async def spinner_wait():
    while True:
        sys.stdout.write(next(spinner))
        sys.stdout.flush()
        sys.stdout.write('\b')
        await asyncio.sleep(0.1)

class Spinner():
    def __init__(self):
        pass
    def __enter__(self):
        # starting a spinner
        self.spinner = asyncio.ensure_future(spinner_wait())
    def __exit__(self, type, value, traceback):
        # got what we needed so we cancel the spinner
        self.spinner.cancel()


base_url = 'https://aoe2.net'

async def get_user(user):
    endpoint = '/api/leaderboard'
    parameters = {'game':'aoe2de', 'leaderboard_id':'4', 'count':'100', 'search':user}
    async with ClientSession() as session:
        async with session.get(base_url+endpoint, params=parameters) as response:
            response = await response.read()
            search_data = json.loads(response)
            for user_data in search_data['leaderboard']:
                if 'name' in user_data and user_data['name'].upper() == user.upper():
                    return user_data
            count = search_data['count']
            print(f'NO USER {count}')
            return []


async def get_user_by_id(steam_id):
    endpoint = '/api/leaderboard'
    parameters = {'game':'aoe2de', 'leaderboard_id':'4', 'count':'100', 'steam_id':steam_id}
    async with ClientSession() as session:
        async with session.get(base_url+endpoint, params=parameters) as response:
            response = await response.read()
            search_data = json.loads(response)
            return search_data


async def get_last_match_for_player(steam_id):
    endpoint = '/api/player/lastmatch'
    parameters = {'game':'aoe2de', 'steam_id':steam_id}
    async with ClientSession() as session:
        async with session.get(base_url+endpoint, params=parameters) as response:
            response = await response.read()
            match_data = json.loads(response)
            match_id = match_data['last_match']['match_id']
            return match_id


async def get_match_data(match_id):
    endpoint = '/api/match'
    parameters = {'game':'aoe2de', 'match_id':match_id}
    async with ClientSession() as session:
        async with session.get(base_url+endpoint, params=parameters) as response:
            response = await response.read()
            match_data = json.loads(response)
            return match_data


async def main():
    user = input("User: ")
    tasks = []

    with Spinner():
        user_data = (await asyncio.gather(asyncio.ensure_future(get_user(user))))[0]
        user_steam_id = user_data['steam_id']
        match_id = (await asyncio.gather(asyncio.ensure_future(get_last_match_for_player(user_steam_id))))[0]

    with Spinner():
        while True:
            await asyncio.sleep(1)
            latest_match_id = (await asyncio.gather(asyncio.ensure_future(get_last_match_for_player(user_steam_id))))[0]
            if latest_match_id != match_id:
                print(f'New match! <{latest_match_id} {match_id}>')
                break
            print('.')
            
        match_data = (await asyncio.gather(asyncio.ensure_future(get_match_data(latest_match_id))))[0]

        # identify teams
        teams = [[],[]]
        for player in match_data['players']:
            match_player_team = player['team']
            match_player_steam_id = player['steam_id']
            teams[match_player_team-1].append(match_player_steam_id)
            if match_player_steam_id == user_steam_id:
                user_last_match_team = match_player_team-1
                user_last_match_oposition_team = 1 if user_last_match_team == 0 else 0

        # get oposition team info
        tasks = []
        for player_id in teams[user_last_match_oposition_team]:
            tasks.append(asyncio.create_task(get_user_by_id(player_id)))
        results = await asyncio.gather(*tasks)

        # print user info
        for task in results:
            data=task['leaderboard'][0]
            print(data['name'], data['previous_rating'], data['wins'], data['losses'])


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()

