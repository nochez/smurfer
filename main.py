import asyncio
import itertools
import sys
import json
import pprint
import pyjq

import prettytable
from prettytable import PrettyTable

from aiohttp import ClientSession
from types import SimpleNamespace
from simple_term_menu import TerminalMenu

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


def print_app_title(version=0):

    header = r""" ___  __  __  __  __  ____  ____  ____  ____  ____ 
/ __)(  \/  )(  )(  )(  _ \( ___)( ___)( ___)(  _ \
\__ \ )    (  )(__)(  )   / )__)  )__)  )__)  )   /
(___/(_/\/\_)(______)(_)\_)(__)  (__)  (____)(_)\_)"""
    print(header)
    print(f'version {version}')
    print('\n')

base_url = 'https://aoe2.net'

async def get_user(user):
    endpoint = '/api/leaderboard'
    parameters = {'game':'aoe2de', 'leaderboard_id':'4', 'count':'100', 'search':user}
    async with ClientSession() as session:
        async with session.get(base_url+endpoint, params=parameters) as response:
            response = await response.read()
            pat = pyjq.compile(f'.leaderboard | map({{name, rating, steam_id}})[] | select(.name=="{user}")')
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


def is_smurf(wins, losses, games):
    few_games = 1 if games < 15 else 0
    mostly_wins = 2 if (wins / (wins + losses)) > 0.55 else 0
    return few_games + mostly_wins


def get_smurfname(smurfcode):
    names = ['normal', 'new account', 'Pitufina', 'PAPA PITUFO']
    return names[smurfcode]

def color_it(data, smurfcode): 
    R = "\033[0;31;40m" #RED
    G = "\033[0;32;40m" # GREEN
    Y = "\033[0;33;40m" # Yellow
    B = "\033[0;34;40m" # Blue
    N = "\033[0m" # Reset

    games_color = [G, Y][smurfcode & 1]
    ratio_color = [G, G, Y, Y][smurfcode & 2]
    smurfname_color = [G, Y, Y, R][smurfcode]
    
    return [smurfname_color+data[0]+N,
            data[1],
            ratio_color+str(data[2])+N,
            ratio_color+str(data[3])+N,
            games_color+str(data[4])+N,
            smurfname_color+data[5]+N]

async def main():
    print_app_title('0.2')
    options = ['Search Ponyo', 'Select by username']
    input_text = ['Ponyo', 'Enter username: ']
    terminal_menu = TerminalMenu(options)
    menu_entry_index = terminal_menu.show()
    
    if menu_entry_index > 0:
        user = input(input_text[menu_entry_index])
    else:
        user = input_text[menu_entry_index]

    tasks = []

    with Spinner():
        print(f'Searching for {user}')
        user_data = (await asyncio.gather(asyncio.ensure_future(get_user(user))))[0]
        if not user_data:
            print('User not found')
            return
        if len(user_data) > 1:
            print(f'Multiple {user} found select one')
            steam_ids = [sub['steam_id'] for sub in user_data]
            user_selection = TerminalMenu(steam_ids)
            user_index = user_selection.show()
            user_steam_id = steam_ids[user_index]
        else:
            user_steam_id = user_data[0]['steam_id']
        match_id = (await asyncio.gather(asyncio.ensure_future(get_last_match_for_player(user_steam_id))))[0]

    with Spinner():
        print(f'Waiting new match for {user}#{user_steam_id}')
        while True:
            await asyncio.sleep(WAIT_BETWEEN_MATCH_LOOKUPS)
            latest_match_id = (await asyncio.gather(asyncio.ensure_future(get_last_match_for_player(user_steam_id))))[0]
            if latest_match_id == match_id:
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

        opposition_team_table = PrettyTable()
        opposition_team_table.field_names = ['Username', 'ELO', 'Wins', 'Loses', 'Games', 'Smurf']
        # print user info
        for task in results:
            data=task['leaderboard'][0]
            smurfcode = is_smurf(data['wins'], data['losses'], data['games'])
            colored_data = color_it([data['name'], data['previous_rating'], data['wins'], data['losses'], data['games'], get_smurfname(smurfcode)], smurfcode)
            opposition_team_table.add_row(colored_data)
        print(opposition_team_table)


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()

