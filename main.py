import asyncio
import itertools
import sys
import json
import pprint
import pyjq

from aiohttp import ClientSession
from types import SimpleNamespace


WAIT_BETWEEN_MATCH_LOOKUPS = 1


# Async spinner print
spinner = itertools.cycle(['ᕕ(⌐■_■)ᕗ',
                           'ᕙ(⌐■_■)ง',
                           'ᕕ(■_■¬)╯',
                           'ᕙ(■_■¬)~'])
async def spinner_wait():
    while True:
        next_spinner = next(spinner)
        sys.stdout.write(next_spinner)
        sys.stdout.flush()
        for x in next_spinner: sys.stdout.write('\b')
        await asyncio.sleep(0.3)

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
            pat = pyjq.compile(f'.leaderboard[] | select(.name=="{user}") | {{name: .name, steam_id: .steam_id}}')
            user_data = pat.all(json.loads(response))
            return user_data


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
        print('Searching for user')
        user_data = (await asyncio.gather(asyncio.ensure_future(get_user(user))))[0]
        if not user_data:
            print('User not found')
            return
        if len(user_data) > 1:
            print("Multiple users found")
            pprint.pprint(user_data)
            return
        pprint.pprint(user_data)
        user_steam_id = user_data[0]['steam_id']
        match_id = (await asyncio.gather(asyncio.ensure_future(get_last_match_for_player(user_steam_id))))[0]

    with Spinner():
        print('Waiting for new match')
        while True:
            await asyncio.sleep(WAIT_BETWEEN_MATCH_LOOKUPS)
            latest_match_id = (await asyncio.gather(asyncio.ensure_future(get_last_match_for_player(user_steam_id))))[0]
            if latest_match_id != match_id:
                print(f'New match found! <{latest_match_id} {match_id}>')
                break
            
        match_data = (await asyncio.gather(asyncio.ensure_future(get_match_data(latest_match_id))))[0]

        # Get opposition team
        # jq explained:
        # from players we sort by team value,
        # then filter only name, id, and team.
        # Finally select the opposite (this is the not part) team entry if any of the members matches the steam id of the user
        query = f'.players | group_by(.team)[] | map({{name, steam_id, team}}) | select( any(.steam_id=="{user_steam_id}") | not )'
        pat = pyjq.compile(query)
        opposition_team = (pat.all(match_data))[0]

        tasks = []
        for player in opposition_team:
            tasks.append(asyncio.create_task(get_user_by_id(player['steam_id'])))
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

