import hashlib
import logging
import os
import sqlite3
from abc import ABC, abstractmethod
from collections import Hashable
from pathlib import Path
from sqlite3 import Connection, Cursor
from threading import Semaphore
from typing import Optional, Iterator

from uuid import uuid4, UUID

logger = logging.getLogger("repository")


class AmongUsFriendsException(Exception):
    pass


class NotFoundException(AmongUsFriendsException):
    pass


class RepositoryException(Exception):
    pass


class NotValidException(RepositoryException):
    pass


class UnknownTypeException(RepositoryException):
    pass


class Markable:
    def __init__(self):
        self._dirty = False

    def mark(self):
        self._dirty = True


class AmongUsConnection(ABC, Markable):
    @abstractmethod
    def cursor(self) -> Cursor:
        raise NotImplementedError()

    @abstractmethod
    def commit(self):
        raise NotImplementedError()

    @abstractmethod
    def rollback(self):
        raise NotImplementedError()


class SqliteDao:
    def __init__(self, connection: AmongUsConnection):
        self.conn = connection


class Lobby:
    def __init__(self, uuid: UUID, title: str, public: bool):
        self.uuid = uuid
        self.title = title
        self.public = public


class Room:
    def __init__(self, uuid: UUID, title: str):
        self.uuid = uuid
        self.title = title


class User:
    def __init__(self, uuid: UUID, username: str, password: str):
        self.uuid = uuid
        self.username = username
        self.password = password


known_conversions = {
    'str': (str, str),
    'int': (int, int),
    'bool': (bool, lambda v: 1 if v else 0),
    'uuid': (UUID, lambda v: v.hex)
}


def sqlite_row(name, fields, *, type_conversions=None, bases=None):
    conv = dict(known_conversions)
    if type_conversions is not None:
        conv.update(type_conversions)
    try:
        fields = [(name, conv[kind]) for name, kind in (col.split(':') for col in fields.split(' '))]
    except KeyError as e:
        raise UnknownTypeException(str(e)) from None

    class SqliteRowPrototype(Hashable):
        rowid: int

        def __init__(self, row):
            self._row = row

        def __repr__(self):
            return f'{self.__class__.__name__}(' + ', '.join(f'{k[0]}={v!r}' for k, v in zip(fields, self._row)) + ')'

        def __eq__(self, other):
            if self.__class__ is not other.__class__:
                return False
            return self.rowid == other.rowid

        def __hash__(self) -> int:
            return hash(self.rowid)

    bases = [SqliteRowPrototype] + (bases if bases is not None else [])

    def _get(index, deserializer):
        def func(self):
            v = self._row[index]
            return None if v is None else deserializer(v)
        return func

    def _set(index, serializer):
        def func(self, val):
            if val is not None:
                val = serializer(val)
            self._row[index] = val
        return func

    t = type(name, tuple(bases), {
        name: property(fget=_get(index, des), fset=_set(index, ser))
        for index, (name, (des, ser)) in enumerate(fields)})
    return t


SqliteLobby = sqlite_row('SqliteLobby', 'rowid:int uuid:uuid title:str anyone:bool')
SqliteMatch = sqlite_row('SqliteMatch', 'rowid:int room_id:int owner:int host:int uuid:uuid title:str end_at:str '
                                        'players:int mode:str map:str result:str network:str')
SqliteRoom = sqlite_row('SqliteRoom', 'rowid:int lobby:int uuid:uuid title:str')
SqliteUser = sqlite_row('SqliteUser', 'rowid:int uuid:uuid username:str password_hash:str')
SqliteUser.secure = property(lambda self: bool(self.password_hash))
SqliteResult = sqlite_row('SqluteResult', 'rowid:int matchid:int user_id:int uuid:uuid r_time:str platform:str '
                                          'color:str imposter:bool victory:bool death:bool comments:str')


class LobbyDao(SqliteDao):
    def create(self, lobby_title: str, public: bool):
        uuid = uuid4()
        c = self.conn.cursor()
        self.conn.mark()
        c.execute('INSERT INTO lobbies (uuid, title, anyone) VALUES (?, ?, ?)',
                  (uuid.hex, lobby_title, public))
        c.close()
        return Lobby(uuid, lobby_title, public)

    def get_by_rowid(self, rowid):
        c = self.conn.cursor()
        c.execute('SELECT * FROM lobbies WHERE rowid == ?', (rowid,))
        row = c.fetchone()
        c.close()
        return SqliteLobby(row)

    def list(self):
        c = self.conn.cursor()
        c.execute('SELECT * FROM lobbies')
        rows = c.fetchall()
        c.close()
        return (SqliteLobby(r) for r in rows)

    def require_lobby(self, room_id: UUID):
        c = self.conn.cursor()
        c.execute("SELECT * FROM lobbies WHERE uuid == ? LIMIT 1", (room_id.hex,))
        row = c.fetchone()
        c.close()
        if row is None:
            raise NotFoundException(room_id)
        return SqliteLobby(row)


class MatchDao(SqliteDao):
    def create(self, match):
        uuid = uuid4()
        c = self.conn.cursor()
        self.conn.mark()
        c.execute('INSERT INTO matches (room_id, owner, host, uuid, title, end_at, players, mode, map, result, network) '
                  'VALUES ('
                  '(SELECT rowid FROM rooms WHERE uuid == ?), '
                  '(SELECT rowid FROM users WHERE uuid == ?), '
                  '(SELECT rowid FROM users WHERE uuid == ?), '
                  '?, ?, ?, ?, ?, ?, ?, ?)',
                  (match.room.uuid.hex, match.owner.uuid.hex, match.host.uuid.hex, uuid.hex, match.title, match.end_at,
                   match.players, match.mode, match.map, match.result, match.network))
        c.close()
        return c.lastrowid

    def list_for_room(self, room):
        c = self.conn.cursor()
        c.execute('SELECT * FROM matches WHERE room_id == '
                  '  (SELECT rowid FROM rooms WHERE uuid == ?)', (room.uuid.hex,))
        rows = c.fetchall()
        c.close()
        return (SqliteMatch(r) for r in rows)


class ResultDao(SqliteDao):
    def create(self, result):
        uuid = uuid4()
        c = self.conn.cursor()
        self.conn.mark()
        c.execute('INSERT INTO results (match_id, user_id, uuid, r_time, platform, color, imposter, victory, death, comments)'
                  'VALUES (?, (SELECT rowid FROM users WHERE uuid == ?), ?, ?, ?, ?, ?, ?, ?, ?)',
                  (result.match_rowid, result.user.uuid.hex, uuid.hex, result.timestamp, result.platform, result.color,
                   result.imposter, result.victory, result.death, result.comments))
        c.close()
        return c.lastrowid

    def counts_by_match_rowid_for_room(self, room):
        c = self.conn.cursor()
        c.execute('SELECT match_id, COUNT(*) FROM results WHERE match_id IN'
                  '  (SELECT rowid FROM matches WHERE room_id == '
                  '    (SELECT rowid FROM rooms WHERE uuid == ?)'
                  '  ) GROUP BY match_id',
                  (room.uuid.hex,))
        counts_by_match_rowid = c.fetchall()
        c.close()
        return counts_by_match_rowid

    def list_for_match(self, match) -> Iterator[SqliteResult]:
        c = self.conn.cursor()
        c.execute('SELECT * FROM results WHERE match_id == (SELECT rowid FROM matches WHERE uuid == ?)',
                  (match.uuid.hex,))
        rows = c.fetchall()
        c.close()
        return (SqliteResult(r) for r in rows)


class RoomDao(SqliteDao):
    def create(self, lobby: Lobby, room_title: str):
        uuid = uuid4()
        c = self.conn.cursor()
        self.conn.mark()
        c.execute('INSERT INTO rooms (lobby_id, uuid, title) VALUES ('
                  '(SELECT rowid FROM lobbies WHERE uuid == ?),'
                  '?, ?)', (lobby.uuid.hex, uuid.hex, room_title,))
        c.close()
        return Room(uuid, room_title)

    def list(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM rooms")
        rows = c.fetchall()
        c.close()
        return (SqliteRoom(r) for r in rows)

    def list_for_lobby(self, lobby: Lobby):
        c = self.conn.cursor()
        c.execute('SELECT * FROM rooms WHERE lobby_id == '
                  '(SELECT rowid FROM lobbies WHERE uuid == ?)', (lobby.uuid.hex,))
        rows = c.fetchall()
        c.close()
        return (SqliteRoom(r) for r in rows)

    def require_room(self, room_id: UUID):
        c = self.conn.cursor()
        c.execute("SELECT * FROM rooms WHERE uuid == ? LIMIT 1", (room_id.hex,))
        row = c.fetchone()
        c.close()
        if row is None:
            raise NotFoundException(room_id)
        return SqliteRoom(row)


class UserDao(SqliteDao):
    def create(self, username, password):
        uuid = uuid4()
        c = self.conn.cursor()
        self.conn.mark()
        c.execute('INSERT INTO users (uuid, username, password) VALUES (?, ?, ?)',
                  (uuid.hex, username, password))
        c.close()
        return User(uuid, username, password)

    def get_by_rowid(self, rowid):
        c = self.conn.cursor()
        c.execute('SELECT * FROM users WHERE rowid == ?', (rowid,))
        row = c.fetchone()
        c.close()
        return SqliteUser(row)

    def list(self):
        c = self.conn.cursor()
        c.execute('SELECT * FROM users')
        users = c.fetchall()
        c.close()
        return users

    def require_user(self, username: str):
        c = self.conn.cursor()
        c.execute('SELECT * FROM users WHERE username == ? LIMIT 1', (username,))
        user = c.fetchone()
        c.close()
        if user is None:
            raise NotFoundException(username)
        return SqliteUser(user)


class Repository(AmongUsConnection):
    def __init__(self, db_path: Path, schema_path: Path):
        super().__init__()
        self.db_path = db_path
        self.schema_path = schema_path
        self._conn: Optional[Connection] = None
        self._active = Semaphore(1)

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._conn.close()
        self._conn = None
        self._active.release()
        if self._dirty:
            self._dirty = False
            if exc_type is None:
                raise ValueError('left repository in a dirty state. changes not committed.')
        return False

    @classmethod
    def _read_schema(cls, schema_path: Path):
        with open(schema_path, 'br') as fp:
            schema = fp.read()
        return schema, hashlib.blake2b(schema).digest()

    @classmethod
    def _first_run(cls, conn: Connection, schema_path: Path):
        schema, schema_hash = cls._read_schema(schema_path)
        s = schema.decode('utf-8')
        conn.executescript(s)
        conn.execute("INSERT INTO meta (hash) VALUES (?)", (schema_hash,))
        conn.commit()

    @classmethod
    def _verify(cls, conn, schema_path: Path):
        schema_hash = cls._read_schema(schema_path)[1]
        try:
            cur = conn.cursor()
            cur.execute("SELECT (hash) FROM meta LIMIT 1")
            row = cur.fetchone()
        except Exception as e:
            raise NotValidException(str(e))
        if row is None:
            raise NotValidException("row was None")
        if schema_hash != row[0]:
            raise NotValidException("different hash")
        return

    def open(self):
        self._active.acquire()
        retry = True
        while self._conn is None and retry:
            existed = self.db_path.exists()
            self._conn = sqlite3.connect(self.db_path)
            try:
                if existed:
                    Repository._verify(self._conn, self.schema_path)
                if not existed:
                    Repository._first_run(self._conn, self.schema_path)
            except Exception as e:
                logger.exception(e)
                self._conn.close()
                self._conn = None
                if isinstance(e, NotValidException):
                    retry = True
                    os.remove(self.db_path)
                else:
                    raise
                continue
            return self
        raise RepositoryException("Could not open the repo.")

    def cursor(self):
        if self._conn is None:
            raise RepositoryException('cannot get cursor. repository is closed.')
        return self._conn.cursor()

    def commit(self):
        self._conn.commit()
        self._dirty = False
        return None

    def rollback(self):
        self._conn.rollback()
        self._dirty = False
        return None

    def lobby_dao(self):
        return LobbyDao(self)

    def match_dao(self):
        return MatchDao(self)

    def result_dao(self):
        return ResultDao(self)

    def room_dao(self):
        return RoomDao(self)

    def user_dao(self):
        return UserDao(self)
