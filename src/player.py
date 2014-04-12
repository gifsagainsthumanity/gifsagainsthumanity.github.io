
all_players = {}
socket_players = {}

class Player:
    def __init__(self, socket, name):
        all_players[socket] = self
        socket_players[self] = socket
        self.name = name
        self.socket = socket


def drop_player(socket):
    if socket in all_players:
        p = all_players[socket]
        del socket_players[p]
        del all_players[socket]

