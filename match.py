import pyjq
import pprint
import asyncio

import search

class Match(object):
    @classmethod
    async def create(cls, mid):
        match_data = await search.match(mid)
        # get match info
        pat = pyjq.compile('{leaderboard_id, map_type, map_size, num_players, victory}')
        match_info = (pat.all(match_data))[0]
        # players
        pat = pyjq.compile('.players[] | {profile_id, team, color, civ}')
        match_players = pat.all(match_data)

        self = Match(match_id=mid, **match_info)
        for player in match_players:
            self.add_player(**player)
        return self

    def __init__(self, match_id, leaderboard_id, map_type, map_size, num_players, victory):
        self.match_id = match_id
        self.leaderboard_id = leaderboard_id
        self.map_type = map_type
        self.map_size = map_size
        self.num_players = num_players
        self.victory = victory
        self.teams = [[], []]

    def add_player(self, profile_id, team, color, civ):
        data = {'profile_id':profile_id, 'color':color, 'civ':civ}
        self.teams[team - 1].append(data)

    def all_players(self):
        return self.teams[0] + self.teams[1]


    def show(self):
        print(self.leaderboard_id, self.map_type, self.map_size, self.num_players, self.teams)


async def main():
    m = await Match.create('133710360')
    m.show()


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
