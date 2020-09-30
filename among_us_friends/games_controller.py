from socket import socket, create_connection
from uuid import UUID

from flask import current_app, json

from among_us_friends.game import Game
from among_us_friends.repository import User


__all__ = ['JsonGame', 'create_game', 'get_game']


class JsonGame(Game):
    def __init__(self, j):
        self._owner = UUID(j['owner_id'])
        self._room = UUID(j['room_id'])
        self._title = j['title']
        self._uuid = UUID(j['game_id'])

    @property
    def owner(self):
        return self._owner

    @property
    def room(self):
        return self._room

    @property
    def title(self):
        return self._title

    @property
    def uuid(self):
        return self._uuid



class GameServiceSocket:
    _socket: socket

    def __init__(self, address):
        self._address = address

    def __enter__(self):
        self._socket = create_connection(self._address)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._socket.close()
        return False

    def send(self, msg: bytes):
        length = str(len(msg)).encode('utf-8') + b'\x00'
        len_len = len(length)
        buff = bytearray(len_len + len(msg))
        buff[:len_len] = length
        buff[len_len:] = msg
        self._socket.send(buff)

    def recv(self):
        buff_size = 4096
        buff = self._socket.recv(buff_size)
        if len(buff) == 0:
            raise ValueError('connection closed')
        s_idx = buff.find(b'\x00')
        if s_idx == -1:
            raise ValueError('did not find size terminator')
        size = int(buff[:s_idx].decode('utf-8'))
        rem = buff_size - s_idx - 1
        if size > rem:
            raise ValueError('could not parse long message')
        return memoryview(buff)[s_idx+1:].tobytes()

    def send_json(self, j):
        return self.send(json.dumps(j).encode('utf-8'))

    def recv_json(self):
        return json.loads(self.recv().decode('utf-8'))


def _service():
    return GameServiceSocket(current_app.config['GAME_SERVICE'])


def create_game(owner: User, room_id: UUID, title: str) -> UUID:
    with _service() as sock:
        sock.send_json({
            'task': 'create_game',
            'owner': owner.uuid.hex,
            'room': room_id,
            'title': title
        })
        return UUID(sock.recv_json()['game_id'])


def get_game(game_id: UUID):
    with _service() as sock:
        sock.send_json({
            'task': 'get_game',
            'game_id': game_id.hex
        })
        return JsonGame(sock.recv_json())


def get_games_for_room(room_id: UUID):
    with _service() as sock:
        sock.send_json({
            'task': 'get_games_for_room',
            'room_id': room_id.hex
        })
        return [JsonGame(j) for j in sock.recv_json()['games']]
