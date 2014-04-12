
all_games = []

class Game:
    def __init__(self):
        all_games.append(self)
        self.players = []


    def join_game(self, player):
        if player not in self.players:
            self.players.append(player)

