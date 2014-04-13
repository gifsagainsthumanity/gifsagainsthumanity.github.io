import struct
import SocketServer
from base64 import b64encode
from hashlib import sha1
from mimetools import Message
from StringIO import StringIO
import threading


import socket, select
import json
from player import Player, all_players
import base64
import hashlib
import struct
from random import randint

all_games = {}

class Game:
    @staticmethod
    def _generate_name():
        with open("data/wordlist") as f:
            content = f.readlines()
        word_list = []
        for word in content:
            word_list.append(word.strip().replace('\n', ''))
        return word_list
    WORD_LIST = _generate_name()

    def __init__(self):
        self.keyword = self.get_keyword()
        all_games[self.keyword] = self
        self.players = []
        self.leader_index = 0
        self.cards = self._generate_cards()
        self.white_cards = self._generate_white_cards()
        self.game_started = False
        self.round_cards = {}
        self.current_score = {}
        self.owner = None

    def get_keyword(self):
        index = randint(0, len(self.WORD_LIST))
        return self.WORD_LIST.pop(index)

    def get_and_next_leader(self):
        index = self.leader_index
        self.leader_index += 1 % len(self.players)
        return self.players[index]

    def get_leader(self):
        return self.players[self.leader_index]

    def draw_card(self):
        index = randint(0, len(self.cards))
        return self.cards.pop(index)

    def draw_white_card(self):
        index = randint(0, len(self.white_cards))
        return self.white_cards.pop(index)

    def start_game(self):
        self.game_started = True

    def join_game(self, player):
        if not self.owner:
            self.owner = player
        if not self.game_started and player not in self.players:
            self.players.append(player)
            self.current_score[player] = 0
            message = json.dumps({
                "action": "lobby_update",
                "lobby": {
                    "players": [{"name": player.name} for player in self.players]
                },
                "keyword": self.keyword,
                "owner": self.owner
            })
            for p in self.players:
                p.socket.send_message(message)

    def play_card(self, card, player):
        self.round_cards[card] = player

    def _generate_cards(self):
        with open("../gifs/list.txt") as f:
            content = f.readlines()
        cards = []
        for card in content:
            cards.append(card.strip().replace('\n', ''))
        return cards

    def _generate_white_cards(self):
        return ["asdsdg", "dwljfgwidf", "jhkfhdkjhfks"]


def user_connected():
    pass

def handle_join(req, socket):
    if "name" not in req:
        print "bad json"
        return

    name = req["name"]
    player = Player(socket, name)
    keyword = req["keyword"]
    if keyword not in all_games:
        return
    game = all_games[keyword]
    game.join_game(player)

    resp = {
        "action": "join",
        "name": name
    }
    js = json.dumps(resp)
    socket.send_message(js)

def handle_create(req, socket):
    if "name" not in req:
        print "bad json"
        return
    name = req["name"]
    player = Player(socket, name)

    game = Game()
    game.join_game(player)

    resp = {
        "action": "create",
        "keyword": game.keyword
    }

    js = json.dumps(resp)
    socket.send_message(js)

def handle_start_game(data, socket):
    if "keyword" not in data:
        print "bad input"
        return
    keyword = data["keyword"]
    game = all_games[keyword]
    game.start_game()
    for player in game.players:
        for i in xrange(0, 7):
            card = game.draw_card()
            message = {
                "action": 'receive_card',
                "card": card
            }
            player.socket.send_message(json.dumps(message))
    leader = game.get_and_next_leader()

    resp = {
        "action":"start_server",
        "leader": leader.name,
        "whitecard": game.draw_white_card()
        }

    for player in game.players:
        r = json.dumps(resp)
        player.socket.send_message(r)

def handle_card_played(data, socket):
    if "keyword" not in data or "card" not in data:
        print "bad data"
        return
    player = all_players[socket]
    keyword = data["keyword"]
    card = data["card"]

    game = all_games[keyword]
    leader = game.get_leader()
    game.play_card(card, player)

    message = {
        "card": card,
        "keyword": keyword,
        "action": "card_played"
    }
    leader.socket.send_message(json.dumps(message))

def handle_card_selected(data, socket):
    if "card" not in data or "keyword" not in data:
        print "bad data"
        return
    card = data["card"]
    keyword = data["keyword"]
    game = all_games[keyword]
    winner = game.round_cards[card]
    game.current_score[winner] += 1

    message = {
        "action": "round_won",
        "card": "card",
        "winner": winner.name,
        "score": game.current_score,
    }
    for player in game.players:
        player.socket.send_message(json.dumps(message))

    winner_message = None
    for player in game.players:
        if game.current_score[player] >= 7:
            winner_message = {
                "action": "game_over",
                "winner": player.name
            }

    if winner_message:
        for player in game.players:
            player.socket.send_message(json.dumps(winner_message))
        del all_games[keyword]
        game.WORD_LIST.append(keyword)

def handle_start_round(data, socket):
    if "keyword" not in data:
        print "bad data"
        return
    keyword = data["keyword"]
    game = all_games[keyword]

    leader = game.get_and_next_leader()
    for player in game.players:
        card = game.draw_card()
        message = {
            "action": 'receive_card',
            "card": card
        }
        player.socket.send_message(json.dumps(message))

    resp = {
        "action":"start_server",
        "leader": leader.name,
        "whitecard": game.draw_white_card()
        }

    for player in game.players:
        r = json.dumps(resp)
        player.socket.send_message(r)


def handle_data_received(data, socket):
    try:
        resp = json.loads(data)
    except:
        print "not JSON"
        return

    if "action" not in resp:
        print "bad request"

    action = resp["action"]
    if action == "create":
        handle_create(resp, socket)
    elif action == "join":
        handle_join(resp, socket)
    elif action == "start_game":
        handle_start_game(resp, socket)
    elif action == "card_played":
        handle_card_played(resp, socket)
    elif action == "select_card":
        handle_card_selected(resp, socket)
    elif action == "start_round":
        handle_start_round(resp, socket)


class WebSocketsHandler(SocketServer.StreamRequestHandler):
    magic = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'

    def setup(self):
        SocketServer.StreamRequestHandler.setup(self)
        print "connection established", self.client_address
        self.handshake_done = False

    def handle(self):
        while True:
            if not self.handshake_done:
                self.handshake()
            else:
                self.read_next_message()

    def finish(self):
        pass

    def read_next_message(self):
        length = ord(self.rfile.read(2)[1]) & 127
        if length == 126:
            length = struct.unpack(">H", self.rfile.read(2))[0]
        elif length == 127:
            length = struct.unpack(">Q", self.rfile.read(8))[0]
        masks = [ord(byte) for byte in self.rfile.read(4)]
        decoded = ""
        for char in self.rfile.read(length):
            decoded += chr(ord(char) ^ masks[len(decoded) % 4])
        handle_data_received(decoded, self)

    def send_message(self, message):
        self.request.send(chr(129))
        length = len(message)
        if length <= 125:
            self.request.send(chr(length))
        elif length >= 126 and length <= 65535:
            self.request.send(126)
            self.request.send(struct.pack(">H", length))
        else:
            self.request.send(127)
            self.request.send(struct.pack(">Q", length))
        self.request.send(message)

    def handshake(self):
        data = self.request.recv(1024).strip()
        headers = Message(StringIO(data.split('\r\n', 1)[1]))
        if headers.get("Upgrade", None) != "websocket":
            return
        print 'Handshaking...'
        key = headers['Sec-WebSocket-Key']
        digest = b64encode(sha1(key + self.magic).hexdigest().decode('hex'))
        response = 'HTTP/1.1 101 Switching Protocols\r\n'
        response += 'Upgrade: websocket\r\n'
        response += 'Connection: Upgrade\r\n'
        response += 'Sec-WebSocket-Accept: %s\r\n\r\n' % digest
        self.handshake_done = self.request.send(response)


class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

if __name__ == "__main__":
    # Port 0 means to select an arbitrary unused port
    HOST, PORT = "", 5000

    server = ThreadedTCPServer((HOST, PORT), WebSocketsHandler)
    ip, port = server.server_address

    # Start a thread with the server -- that thread will then start one
    # more thread for each request
    server_thread = threading.Thread(target=server.serve_forever)
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()
    print "Server loop running in thread:", server_thread.name
    server.serve_forever()