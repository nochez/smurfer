import asyncio
import json
import pprint
import pyjq
import prettytable

from prettytable import PrettyTable
from aiohttp import ClientSession
from types import SimpleNamespace
from simple_term_menu import TerminalMenu

import search
from match import Match
from player import Player
from spinner import Spinner

WAIT_BETWEEN_MATCH_LOOKUPS = 1

def print_app_title(version=0):

    header = r""" ___  __  __  __  __  ____  ____  ____  ____ 
/ __)(  \/  )(  )(  )(  _ \( ___)( ___)(  _ \
\__ \ )    (  )(__)(  )   / )__)  )__)  )   /
(___/(_/\/\_)(______)(_)\_)(__)  (____)(_)\_)"""
    print(header)
    print(f'version {version}')
    print('\n')


async def main():
    print_app_title('0.5')
    options = ['Search Camacho', 'Select by username']
    input_text = ['Camacho', 'Enter username: ']
    terminal_menu = TerminalMenu(options)
    menu_entry_index = terminal_menu.show()
    
    if menu_entry_index > 0:
        user = input(input_text[menu_entry_index])
    else:
        user = input_text[menu_entry_index]

    with Spinner():
        print(f'Searching for {user}')
        profiles = list(await search.profile_id(user))
        if not profiles:
            print('User not found')
            return
        if len(profiles) > 1:
            print(f'Multiple {user} found select one')
            user_selection = TerminalMenu(profiles)
            user_index = user_selection.show()
            user_profile_id = profiles[user_index]
        else:
            user_profile_id = profiles[0]
        ref_player = await Player.create(user_profile_id)
        match_id = (await asyncio.gather(asyncio.ensure_future(search.last_match_id(ref_player.profile_id))))[0]

    options = ['Search for new match', 'Look latest match']
    print("Select what match to compare")
    match_query = TerminalMenu(['New match', 'Latest match']).show()

    with Spinner():
        print(f'Waiting match for {user}#{ref_player.profile_id}: ELO#{ref_player.team_rating}')
        while True:
            await asyncio.sleep(WAIT_BETWEEN_MATCH_LOOKUPS)
            latest_match_id = (await asyncio.gather(asyncio.ensure_future(search.last_match_id(ref_player.profile_id))))[0]
            match_found = (latest_match_id == match_id) if match_query else (latest_match_id != match_id) 
            if match_found:
                print(f'Match found! <{latest_match_id} {match_id}>')
                break

        # process match
        match = await Match.create(latest_match_id)
        # for every team get player data then print the info
        for team_number in [0, 1]:
            tasks = []
            for player in match.teams[team_number]:
                tasks.append(asyncio.create_task(Player.create(player['profile_id'])))
            results = await asyncio.gather(*tasks)

            print_team(team_number, results)
                

def color_it(data, smurfcode, ref_elo):
    R = "\033[0;31;40m" #RED
    G = "\033[0;32;40m" # GREEN
    Y = "\033[0;33;40m" # Yellow
    B = "\033[0;34;40m" # Blue
    N = "\033[0m" # Reset

    games_color = [N, Y][smurfcode & 1]
    ratio_color = [N, N, Y, Y][smurfcode & 2]
    smurfname_color = [N, Y, Y, R][smurfcode]
    
    elo_range_dif = [abs((data[1] - ref_elo) - x) for x in [-50, 0, 40, 100]]
    min_index = elo_range_dif.index(min(elo_range_dif))
    elo_color = [G, N, Y, R][min_index]


    return [smurfname_color+data[0]+N,
            elo_color+str(data[1])+N,
            ratio_color+str(data[2])+N,
            ratio_color+str(data[3])+N,
            games_color+str(data[4])+N,
            smurfname_color+data[5]+N]


def print_team(team_number, players):
    team_table = PrettyTable()
    team_table.title = 'Team #' + str(team_number)
    team_table.field_names = ['Name', 'SE', 'SR', 'SG', 'TE', 'TR', 'TG', 'SMURF']
    for player in players:
        team_table.add_row([player.name,
            player.single_rating,
            str(player.single_wins)+'/'+str(player.single_losses),
            player.single_games,
            player.team_rating,
            str(player.team_wins)+'/'+str(player.team_losses),
            player.team_games,
            Player.smurfname(player.is_team_smurf())])
    print(team_table)


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()

