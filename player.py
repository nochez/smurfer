import pyjq
import pprint
import asyncio

from aoe2net import call_aoe2net


class Player(object):
    # Use factory pattern to create players due to asyncio use
    @classmethod
    async def create(cls, profile_id):
        user_data = {'profile_id': profile_id}
        endpoint = '/api/leaderboard'
        # single player data
        parameters_single = {'game': 'aoe2de', 'count':'1', 'profile_id': profile_id, 'leaderboard_id': '3'}
        single_player_data = await call_aoe2net(endpoint, parameters_single)
        if single_player_data['count'] == 1:
            single_jq = '.leaderboard[] | ' \
                        '{name, country, clan, ' \
                        '"single_rating":.rating, ' \
                        '"single_wins":.wins, ' \
                        '"single_losses": .losses, ' \
                        '"single_games":.games}'
            single_query = pyjq.compile(single_jq)
            user_data = user_data | (single_query.all(single_player_data))[0]
        # team player data
        parameters_team = {'game': 'aoe2de', 'count':'1', 'profile_id': profile_id, 'leaderboard_id': '4'}
        team_player_data = await call_aoe2net(endpoint, parameters_team)
        if team_player_data['count'] == 1:
            team_jq =   '.leaderboard[] | ' \
                        '{name, country, clan, ' \
                        '"team_rating":.rating, ' \
                        '"team_wins":.wins, ' \
                        '"team_losses": .losses, ' \
                        '"team_games":.games}'
            team_query = pyjq.compile(team_jq)
            user_data = user_data | (team_query.all(team_player_data))[0]
        # player data into an instance
        self = Player()
        self.load(user_data)
        return self

    def load(self, data):
        # default values
        self.name = self.country = self.clan = 'none'
        self.single_rating = self.single_wins = self.single_losses = self.single_games = 0
        self.team_rating = self.team_wins = self.team_losses = self.team_games = 0
        # values we get in a dict
        for key in data:
            setattr(self, key, data[key])

    def show(self):
        attributes = vars(self)
        print(', '.join("%s: %s" % item for item in attributes.items()))

    def is_team_smurf(self):
        few_games = 1 if self.team_games < 15 else 0
        if self.team_games > 0:
            mostly_wins = 2 if (self.team_wins / (self.team_wins + self.team_losses)) > 0.55 else 0
        else: mostly_wins = 2
        return few_games + mostly_wins

    @classmethod
    def smurfname(cls, code):
        names = ['normal', 'new account', 'Pitufina', 'PAPA PITUFO']
        return names[code]


async def main():
    p = await Player.create(5864674) # with all
    p = await Player.create(2027742) # without 1v1
    #p = await Player.create(6139984) # without 1v1
    p.show()


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()

