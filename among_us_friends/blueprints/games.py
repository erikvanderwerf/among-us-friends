from uuid import UUID

from flask import Blueprint, render_template, url_for
from flask_login import login_required, current_user
from werkzeug.exceptions import Unauthorized
from werkzeug.utils import redirect

from among_us_friends import games_controller
from among_us_friends.blueprints import open_repository
from among_us_friends.game import Game

games = Blueprint('games', __name__)


@games.route('/games/<game_id>')
@login_required
def game(game_id):
    game: Game = games_controller.get_game(UUID(game_id))
    admin_rights = game.owner_id = current_user.uuid
    return render_template('game.html', game=game, admin_rights=admin_rights, user=current_user)


@games.route('/games/<game_id>/delete')
@login_required
def delete(game_id):
    uuid = UUID(game_id)
    with open_repository() as repo:
        game = Game(repo, uuid)
        if current_user.uuid != game.owner.uuid:
            raise Unauthorized()
        room = repo.room_dao().get_by_rowid(game.room_id)
        repo.game_dao().delete_by_uuid(uuid)
        repo.commit()
    return redirect(url_for('rooms.room', room_id=room.uuid.hex))


@games.route('/games/<game_id>/admin')
@login_required
def game_admin(game_id):
    with open_repository() as repo:
        game = Game(repo, UUID(game_id))
        if current_user.uuid != game.owner.uuid:
            raise Unauthorized()
        return render_template('game_admin.html', game=game, user=current_user)


@games.route('/games/<game_id>/admin', methods=['POST'])
@login_required
def game_admin_post(game_id):
    with open_repository() as repo:
        repo.match_dao().create()
