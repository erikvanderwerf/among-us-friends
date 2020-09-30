import json
import logging
from uuid import UUID

from among_us_friends.service.service import GameService, Game

logger = logging.getLogger('service.game_manipulation')


def ser_game(game: Game):
    return {
        'game_id': game.uuid.hex,
        'title': game.title,
        'owner_id': game.owner.hex,
        'room_id': game.room.hex
    }


async def create_game(service: GameService, msg):
    builder = service.create_game()
    builder.title = msg['title']
    builder.owner = UUID(msg['owner'])
    builder.room = UUID(msg['room'])
    game_id = await builder.build()
    logger.info('new game ' + game_id.hex)
    return json.dumps({
        'game_id': game_id.hex
    }).encode('utf-8')


async def get_game(service: GameService, msg):
    game: Game = service.games[UUID(msg['game_id'])]
    return json.dumps(ser_game(game)).encode('utf-8')


async def get_game_for_room(service: GameService, msg):
    room_id = UUID(msg['room_id'])

    async with service.games_lock:
        return json.dumps({'games': [ser_game(g) for g in service.games.values() if g.room == room_id]}).encode('utf-8')
