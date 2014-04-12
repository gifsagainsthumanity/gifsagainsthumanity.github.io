
import socket, select
import json
from player import Player, all_players
import base64
import hashlib
import struct
from random import randint

all_games = {}

class Game:
    def __init__(self):
        self.keyword = self._generate_name()
        all_games[self.keyword] = self
        self.players = []
        self.leader_index = 0
        self.cards = self._generate_cards()
        self.white_cards = self._generate_white_cards()
        self.game_started = False
        self.round_cards = {}
        self.current_score = {}

    def get_and_next_leader(self):
        index = self.leader_index
        self.leader_index += 1 % len(self.players)
        return self.players[index]

    def get_leader(self):
        return self.players[self.leader_index]

    def draw_card(self):
        return self.cards.pop()

    def draw_white_card(self):
        return self.white_cards.pop()

    def start_game(self):
        self.game_started = True

    def join_game(self, player):
        if not self.game_started and player not in self.players:
            self.players.append(player)
            self.current_score[player] = 0
            message = json.dumps({
                "action": "player_joined",
                "name": player.name
            })
            for p in self.players:
                broadcast_data(p.socket, message)

    def play_card(self, card, player):
        self.round_cards[card] = player

    def _generate_name(self):
        with open("data/wordlist") as f:
            content = f.readlines()
        word_list = []
        for word in content:
            word_list.append(word.strip().replace('\n', ''))

        index = randint(0, len(word_list))
        word = word_list[index]
        del word_list[index]
        return word

    def _generate_cards(self):
        with open("../gifs/list.txt") as f:
            content = f.readlines()
        cards = []
        for card in content:
            cards.append(card.strip().replace('\n', ''))
        return cards

    def _generate_white_cards(self):
        return ["asdsdg", "dwljfgwidf", "jhkfhdkjhfks"]

def drop_game(keyword):
    del all_games[keyword]


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
    broadcast_data(socket, js)

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
    broadcast_data(socket, js)

def handle_start_game(data, socket):
    if "keyword" not in data:
        print "bad input"
        return
    keyword = data["keyword"]
    game = all_games[keyword]
    game.start_game()
    for player in game.players:
        for i in xrange(0, 2):
            card = game.draw_card()
            message = {
                "action": 'receive_card',
                "card": card
            }
            broadcast_data(player.socket, json.dumps(message))
    leader = game.get_and_next_leader()

    resp = {
        "action":"start_server",
        "leader": leader.name,
        "whitecard": game.draw_white_card()
        }

    for player in game.players:
        r = json.dumps(resp)
        broadcast_data(player.socket, r)

def handle_card_played(data, socket):
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
    broadcast_data(leader.socket, json.dumps(message))

def handle_card_selected(data, socket):

    card = data["card"]
    keyword = data["keyword"]
    game = all_games[keyword]
    winner = game.round_cards[card]
    game.current_score[winner] += 1

    message = {
        "action":"round_won",
        "card": "card",
        "winner": winner.name,
        "score": game.current_score,
    }
    for player in game.players:
        broadcast_data(player.socket, message)

    winner_message = None
    for player in game.players:
        if game.current_score[player] >= 7:
            winner_message = {
                "action": "game_over",
                "winner": player.name
            }

    if winner_message:
        for player in game.players:
            broadcast_data(player.socket, message)

def handle_start_round(data, socket):
    keyword = data["keyword"]
    game = all_games[keyword]

    leader = game.get_and_next_leader()
    for player in game.players:
        card = game.draw_card()
        message = {
            "action": 'receive_card',
            "card": card
        }
        broadcast_data(player.socket, json.dumps(message))

    resp = {
        "action":"start_server",
        "leader": leader.name,
        "whitecard": game.draw_white_card()
        }

    for player in game.players:
        r = json.dumps(resp)
        broadcast_data(player.socket, r)

def do_handshake(data, socket):
    websocket_answer = (
    'HTTP/1.1 101 Switching Protocols',
    'Upgrade: websocket',
    'Connection: Upgrade',
    'Sec-WebSocket-Accept: {key}\r\n\r\n',)

    for line in data.split('\n'):
        line = line.strip()
        parts = line.split(':')
        if parts[0].strip() == "Sec-WebSocket-Key":
            key = parts[1].strip()
            response_key = base64.b64encode(hashlib.sha1(key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").digest())
            response = '\r\n'.join(websocket_answer).format(key=response_key)
            broadcast_data(socket, response)


def handle_data_received(data, socket):
    if data[0] != '{':
       do_handshake(data, socket)
       return
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


#Function to broadcast chat messages to all connected clients
def broadcast_data(sock, message):
    for socket in CONNECTION_LIST:
        if socket != server_socket and socket == sock:
            try:
                socket.send(chr(129))
                length = len(message)
                if length <= 125:
                    socket.send(chr(length))
                elif length >= 126 and length <= 65535:
                    socket.send(126)
                    socket.send(struct.pack(">H", length))
                else:
                    socket.send(127)
                    socket.send(struct.pack(">Q", length))
                socket.send(message)
            except Exception, e:
                # broken socket connection may be, chat client pressed ctrl+c for example
                print "broken socket " + str(e)
                socket.close()
                CONNECTION_LIST.remove(socket)

if __name__ == "__main__":
    # List to keep track of socket descriptors
    CONNECTION_LIST = []
    RECV_BUFFER = 4096 # Advisable to keep it as an exponent of 2
    PORT = 5000

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # this has no effect, why ?
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", PORT))
    server_socket.listen(10)

    # Add server socket to the list of readable connections
    CONNECTION_LIST.append(server_socket)

    print "server started on port " + str(PORT)

    while 1:
        # Get the list sockets which are ready to be read through select
        read_sockets, write_sockets, error_sockets = select.select(CONNECTION_LIST, [], [])

        for sock in read_sockets:
            #New connection
            if sock == server_socket:
                # Handle the case in which there is a new connection recieved through server_socket
                sockfd, addr = server_socket.accept()
                CONNECTION_LIST.append(sockfd)
                print "Client (%s, %s) connected" % (sockfd, addr)

                user_connected()
                # broadcast_data(sockfd, "[%s:%s] entered room\n" % (sockfd, addr))

            #Some incoming message from a client
            else:
                # Data recieved from client, process it
                try:
                    #In Windows, sometimes when a TCP program closes abruptly,
                    # a "Connection reset by peer" exception will be thrown
                    data = sock.recv(RECV_BUFFER)
                    if data:
                        handle_data_received(data, sock)
                        # broadcast_data(sock, "\r" + '<' + str(sock.getpeername()) + '> ' + data)

                except Exception, e:
                    print str(e)
                    broadcast_data(sock, "Client (%s, %s) is offline" % (sockfd, addr))
                    print "Client (%s, %s) is offline" % (sockfd, addr)
                    sock.close()
                    CONNECTION_LIST.remove(sock)
                    continue

    server_socket.close()
