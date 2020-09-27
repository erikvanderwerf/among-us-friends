import csv
import json
from datetime import datetime
from pathlib import Path
from sqlite3 import IntegrityError

from among_us_friends.repository import Repository

DB_PATH = Path('../server/db.sqlite')
SCHEMA_PATH = Path('../server/schema.sql')

USER_FILE = Path('users.json')
MATCH_FILE = Path('gameroot-2020-09-26-14-46.csv')
RESULT_FILE = Path('survey-2020-09-26-14-46.csv')


fuzz_police = {}


def main():
    DB_PATH.unlink(missing_ok=True)  # TODO debug

    de_fuzz_usernames()
    if not DB_PATH.exists():
        collect()


def de_fuzz_usernames():
    with open(USER_FILE) as fp:
        j = json.load(fp)
    for unique, fuzz in j.items():
        for f in fuzz:
            if f in fuzz_police:
                raise ValueError(f'Non unique fuzzy name {f!r} assigned to {fuzz_police[f]!r} and {unique!r}.')
            fuzz_police[f] = unique


def get_by_fuzzy_username(fuzzy):
    with Repository(DB_PATH, SCHEMA_PATH) as repo:
        return repo.user_dao().require_user(fuzz_police[fuzzy.strip()])


class CsvRowMatch:
    def __init__(self, row, room):
        # self._row = row
        self.title = row[0]
        self.room = room
        self.owner = get_by_fuzzy_username(row[8])
        self.host = get_by_fuzzy_username(row[7])
        self.end_at = datetime.strptime(row[1].strip(), '%m/%d/%Y %H:%M:%S').isoformat()
        self.players = int(row[2])
        self.mode = row[3].strip()
        self.map = row[4].strip()
        self.result = row[5].strip()
        self.network = row[6].strip()


class CsvRowResult:
    def __init__(self, row, match_map):
        # self._row = row
        self.timestamp = datetime.strptime(row[0].strip(), '%m/%d/%Y %H:%M:%S').isoformat()
        self.match_rowid = match_map[row[1].strip()]
        self.user = get_by_fuzzy_username(row[2])
        self.username = row[3].strip()
        self.platform = row[4].strip().lower()
        self.color = row[5].strip().lower()
        self.imposter = bool(row[6].strip() == 'Yes')
        self.victory = bool(row[7].strip() == 'Yes')
        self.death = bool(row[8].strip() == 'Yes')
        self.comments = row[9].strip()


def collect():
    # Known Users
    with Repository(DB_PATH, SCHEMA_PATH) as repo:
        for name in set(fuzz_police.values()):
            repo.user_dao().create(name, None)
            repo.commit()

    # Create Room
    with Repository(DB_PATH, SCHEMA_PATH) as repo:
        lobby = repo.lobby_dao().create('Friends', True)
        room = repo.room_dao().create(lobby, 'main')
        repo.commit()

    # Matches
    with open(MATCH_FILE) as fp:
        matches = iter(list((csv.reader(fp))))
    next(matches)  # Skip header
    matches = [CsvRowMatch(m, room) for m in matches]
    match_title_row = {}
    with Repository(DB_PATH, SCHEMA_PATH) as repo:
        for match in matches:
            match_title_row[match.title] = repo.match_dao().create(match)
        repo.commit()

    # Results
    with open(RESULT_FILE) as fp:
        results = iter(list(csv.reader(fp)))
    next(results)
    results = [CsvRowResult(r, match_title_row) for r in results]
    with Repository(DB_PATH, SCHEMA_PATH) as repo:
        try:
            for result in results:
                repo.result_dao().create(result)
        except IntegrityError as e:
            raise ValueError('Problem with result ' + str(result.match_rowid) + ' on ' + str(result.user.username)) from e
        repo.commit()

        print('\n'.join(repo._conn.iterdump()))


if __name__ == '__main__':
    main()
