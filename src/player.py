all_players = {}

class Player:
    def __init__(self, socket, name):
        all_players[socket] = self
        self.name = name


def drop_player(socket):
    if socket in all_players:
        del all_players[socket]

