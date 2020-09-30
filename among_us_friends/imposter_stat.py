from typing import Iterable

from among_us_friends.repository import SqliteResult


class ImposterStat:
    def __init__(self, title: str):
        self.title: str = title
        self.total_matches: int = 0
        self.times_imposter: int = 0
        self.deviation: float = 0.0
        self.wins_crew: int = 0
        self.wins_imposter: int = 0
        self.loss_crew: int = 0
        self.loss_imposter: int = 0
        self.imposter_counts = {1: 0, 2: 0, 3: 0}

    @property
    def times_crew(self):
        return self.total_matches - self.times_imposter

    @property
    def i_counts(self):
        return f'{self.imposter_counts[1]}/{self.imposter_counts[2]}/{self.imposter_counts[3]}'

    @property
    def wins_crew_pct(self):
        try:
            pct = round(100 * self.wins_crew / self.times_crew)
        except ZeroDivisionError:
            pct = 'NA'
        return f'{pct}%'

    @property
    def wins_imposter_pct(self):
        try:
            pct = round(100 * self.wins_imposter / self.times_imposter)
        except ZeroDivisionError:
            pct = 'NA'
        return f'{pct}%'

    @property
    def loss_crew_pct(self):
        try:
            pct = round(100 * self.loss_crew / self.times_crew)
        except ZeroDivisionError:
            pct = 'NA'
        return f'{pct}%'

    @property
    def loss_imposter_pct(self):
        try:
            pct = round(100 * self.loss_imposter / self.times_imposter)
        except ZeroDivisionError:
            pct = 'NA'
        return f'{pct}%'

    def tablulate(self, match, match_num_imposters, result: SqliteResult):
        self.total_matches += 1
        self.times_imposter += int(result.imposter)
        self.deviation += (
            (-1 / (match.players - match_num_imposters)) if not result.imposter else (1.0 / match_num_imposters))
        self.wins_crew += int(not result.imposter and result.victory)
        self.wins_imposter += int(result.imposter and result.victory)
        self.loss_crew += int(not result.imposter and not result.victory)
        self.loss_imposter += int(result.imposter and not result.victory)
        if result.imposter:
            self.imposter_counts[match_num_imposters] += 1


class HtmlImposterStatsFormatter:
    def __init__(self, imposters: Iterable[ImposterStat]):
        self.imposters = imposters

    def format(self):
        fmt = '<table><tr>' \
              '<th>Title</th>' \
              '<th>#Matches</th>' \
              '<th>#Imposter</th>' \
              '<th>Deviation</th>' \
              '<th>Wins Crewmate</th>' \
              '<th>Wins Imposter</th>' \
              '<th>Losses Crewmate</th>' \
              '<th>Losses Imposter</th>' \
              '</tr>'
        for p in sorted(self.imposters, key=lambda k: k.total_matches, reverse=True):
            fmt += '<tr>' \
                   f'<td>{p.title}</td>' \
                   f'<td>{p.total_matches}</td>' \
                   f'<td><b>{p.times_imposter}</b> {p.i_counts}</td>' \
                   f'<td>{round(p.deviation, 2)}</td>' \
                   f'<td>{p.wins_crew} / {p.wins_crew_pct}</td>' \
                   f'<td>{p.wins_imposter} / {p.wins_imposter_pct}</td>' \
                   f'<td>{p.loss_crew} / {p.loss_crew_pct}</td>' \
                   f'<td>{p.loss_imposter} / {p.loss_imposter_pct}</td>' \
                   '</tr>'
        fmt += '</table>'
        return fmt
