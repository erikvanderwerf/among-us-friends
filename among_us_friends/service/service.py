from asyncio.locks import Lock

from uuid import uuid4, UUID


class Game:
    def __init__(self, uuid, title, owner, room):
        self._lock = Lock()
        self.uuid = uuid
        self.title = title
        self.owner = owner
        self.room = room


class GameBuilder:
    title: str
    owner: UUID
    room: UUID

    def __init__(self, cb):
        self._cb = cb

    def build(self):
        return self._cb(Game(None, self.title, self.owner, self.room))


class GameService:
    def __init__(self):
        self.games = {}
        self.games_lock = Lock()

    def create_game(self):
        async def build(game: Game):
            async with self.games_lock:
                game_id = uuid4()
                game.uuid = game_id
                self.games[game_id] = game
            return game_id
        return GameBuilder(build)
