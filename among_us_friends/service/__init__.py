import asyncio
import json
import logging
from asyncio.streams import StreamReader, StreamWriter

from among_us_friends.service import game_manipulation
from among_us_friends.service.service import GameService


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('service')


SERVICE: GameService


_TASK_HANDLER = {
    'create_game': game_manipulation.create_game,
    'get_game': game_manipulation.get_game,
    'get_games_for_room': game_manipulation.get_game_for_room
}


async def read_msg(reader: StreamReader) -> bytes:
    buff_size = 4096
    buff = await reader.read(buff_size)
    if len(buff) == 0:
        return buff
    s_idx = buff.find(b'\x00')
    if s_idx == -1:
        raise ValueError('did not find size terminator')
    size = int(buff[:s_idx].decode('utf-8'))
    rem = buff_size - s_idx - 1
    if size > rem:
        raise ValueError('could not parse long message')
    return memoryview(buff)[s_idx + 1:].tobytes()


async def write_msg(writer: StreamWriter, msg: bytes):
    length = str(len(msg)).encode('utf-8') + b'\x00'
    len_len = len(length)
    buff = bytearray(len_len + len(msg))
    buff[:len_len] = length
    buff[len_len:] = msg
    writer.write(buff)


async def run_service():
    global SERVICE
    SERVICE = GameService()
    server = await asyncio.start_server(open_connection, port=4700)
    await server.serve_forever()


async def open_connection(reader: StreamReader, writer: StreamWriter):
    logger.info('opened new socket')
    while True:
        read = await read_msg(reader)
        if len(read) == 0:
            break
        msg = json.loads(read.decode('utf-8'))
        try:
            task = _TASK_HANDLER[msg['task']]
        except KeyError:
            logger.exception('Could not find requested task.')
            break
        try:
            reply = await task(SERVICE, msg)
        except Exception:
            logger.exception('Problem with handler: ' + msg['task'])
            break
        await write_msg(writer, reply)
    writer.close()
    logger.info('closed socket')
