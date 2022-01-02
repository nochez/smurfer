import pyjq
import pprint
import asyncio

from aoe2net import call_aoe2net

# get profile id for a username and returns a set with all found profile_id
async def profile_id(username):
    endpoint = '/api/leaderboard'
    # user could be in any of the leaderboards but we should search 3 and 4
    profiles = set()
    for leaderboard in [3, 4]:
        parameters = {'game': 'aoe2net', 'count':'100', 'leaderboard_id':str(leaderboard), 'search':username}
        user_data = await call_aoe2net(endpoint, parameters)
        if user_data['count'] != 0:
            pat = pyjq.compile(f'.leaderboard[] | select(.name=="{username}") | {{profile_id}}')
            entries = pat.all(user_data)
            for entry in entries:
                profiles.add(str(entry['profile_id']))
    return profiles


async def last_match_id(profile_id):
    endpoint = '/api/player/lastmatch'
    parameters = {'game': 'aoe2de', 'profile_id' : profile_id}
    match_data = await call_aoe2net(endpoint, parameters)
    return match_data['last_match']['match_id']


async def match(match_id):
    endpoint = '/api/match'
    parameters = {'game': 'aoe2net', 'match_id': match_id}
    match_data = await call_aoe2net(endpoint, parameters)
    return match_data


async def main():
    await profile_id('Ponyo')
    await profile_id('Nemo')

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()

