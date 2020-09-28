from flask import url_for


class HtmlGamesFormatter:
    def __init__(self, games):
        self.games = games

    def format(self):
        fmt = '<ol>'
        for game in self.games:
            fmt += f'''<li><a href="{url_for('games.game', game_id=game.uuid.hex)}">{game.title}</a></li>'''
        fmt += '</ol>'
        return fmt
