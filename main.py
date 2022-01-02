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

def is_smurf(wins, losses, games):
    few_games = 1 if games < 15 else 0
    mostly_wins = 2 if (wins / (wins + losses)) > 0.55 else 0
    return few_games + mostly_wins


def get_smurfname(smurfcode):
    names = ['normal', 'new account', 'Pitufina', 'PAPA PITUFO']
    return names[smurfcode]

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

async def main():
    print_app_title('0.4')
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
            user_profile_id = user_data[0]
        ref_player = await Player.create(user_profile_id)
        #match_id = (await asyncio.gather(asyncio.ensure_future(get_last_match_for_player(ref_player.profile_id))))[0]
        match_id = (await asyncio.gather(asyncio.ensure_future(search.last_match_id(ref_player.profile_id))))[0]

    options = ['Search for new match', 'Look latest match']
    print("Select what match to compare")
    match_query = TerminalMenu(['New match', 'Latest match']).show()


    with Spinner():
        print(f'Waiting new match for {user}#{ref_player.profile_id}: ELO#{ref_player.team_rating}')
        while True:
            await asyncio.sleep(WAIT_BETWEEN_MATCH_LOOKUPS)
            #latest_match_id = (await asyncio.gather(asyncio.ensure_future(get_last_match_for_player(ref_player.profile_id))))[0]
            latest_match_id = (await asyncio.gather(asyncio.ensure_future(search.last_match_id(ref_player.profile_id))))[0]
            match_found = (latest_match_id == match_id) if match_query else (latest_match_id != match_id) 
            if match_found:
                print(f'Match found! <{latest_match_id} {match_id}>')
                break
            
        match_data = (await asyncio.gather(asyncio.ensure_future(search.match(latest_match_id))))[0]

        # Get opposition team
        # jq explained:
        # from players we sort by team value,
        # then filter only name, id, and team.
        # Finally select the opposite (this is the not part) team entry if any of the members matches the profile id of the user
        query = f'.players | group_by(.team)[] | map({{name, profile_id, team}}) | select( any(.profile_id=={ref_player.profile_id}) | not )'
        pat = pyjq.compile(query)
        opposition_team = (pat.all(match_data))[0]
        #pprint.pprint(match_data)
        #pprint.pprint(opposition_team)

        tasks = []
        for player in opposition_team:
            tasks.append(asyncio.create_task(Player.create(player['profile_id'])))
        results = await asyncio.gather(*tasks)

        opposition_team_table = PrettyTable()
        opposition_team_table.field_names = ['Username', 'ELO', 'Wins', 'Loses', 'Games', 'Smurf']
        # print user info
        for player in results:
            smurfcode = is_smurf(player.team_wins, player.team_losses, player.team_games)
            colored_data = color_it([player.name, player.team_rating, player.team_wins, player.team_losses, player.team_games, get_smurfname(smurfcode)], smurfcode, ref_player.team_rating)
            opposition_team_table.add_row(colored_data)
        print(opposition_team_table)


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()

