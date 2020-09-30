from uuid import UUID

from flask import Blueprint, render_template, request, url_for
from flask_login import login_required, current_user
from werkzeug.exceptions import abort
from werkzeug.utils import redirect

from among_us_friends import games_controller
from among_us_friends.blueprints import open_repository
from among_us_friends.room_correlations import HtmlRoomCorrelationsFormatter, RoomCorrelations
from among_us_friends.games import HtmlGamesFormatter
from among_us_friends.imposter_stat import HtmlImposterStatsFormatter
from among_us_friends.stats import PlayersMatchesStats, ColorsMatchesStats
from among_us_friends.repository import NotFoundException

rooms = Blueprint('rooms', __name__)


@rooms.route("/rooms/<room_id>")
@login_required
def room(room_id):
    mode = request.args.get('mode', '%')
    room_uuid = UUID(room_id)
    games = games_controller.get_games_for_room(room_uuid)
    print(games)
    with open_repository() as repo:
        try:
            room = repo.room_dao().require_room(room_uuid)
        except NotFoundException:
            abort(404)
        matches = list(repo.match_dao().list_for_room(room, mode))
        lobby_id = repo.lobby_dao().get_by_rowid(room.lobby).uuid.hex
        counts = repo.result_dao().counts_by_match_rowid_for_room(room)
        player_stats = list(PlayersMatchesStats(matches).using(repo))
        color_stats = list(ColorsMatchesStats(matches).using(repo))
        correlations = RoomCorrelations(room, matches).using(repo)
    counts = dict(counts)
    matches = {m.rowid: m for m in matches}
    match_counts = ((matches.get(k, None), counts.get(k, None)) for k in counts.keys() | matches.keys())
    return render_template(
        'room.html', room=room, match_counts=match_counts, user=current_user,
        lobby=lobby_id,
        games=HtmlGamesFormatter(games),
        player_stats=HtmlImposterStatsFormatter(player_stats),
        color_stats=HtmlImposterStatsFormatter(color_stats),
        correlations=HtmlRoomCorrelationsFormatter(correlations)
    )


@rooms.route('/rooms/<room_id>/createGame', methods=['GET', 'POST'])
@login_required
def create_game(room_id):
    if request.method == 'GET':
        return render_template('new_game.html')
    title = request.form['title']
    user = current_user
    game_id = games_controller.create_game(user, room_id, title)
    return redirect(url_for('games.game', game_id=game_id))
