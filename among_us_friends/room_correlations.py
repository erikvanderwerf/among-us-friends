from among_us_friends.repository import Repository


class RoomCorrelations:
    def __init__(self, room, matches):
        self._room = room
        self._matches = matches
        self._chosen_probability = None

    def using(self, repo: Repository):
        pass


class HtmlRoomCorrelationsFormatter:
    def __init__(self, correlations: RoomCorrelations):
        self.corr = correlations

    def format(self):
        return 'Hello'
