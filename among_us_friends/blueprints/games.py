from uuid import UUID

from flask import Blueprint, render_template, url_for
from flask_login import login_required, current_user
from werkzeug.exceptions import NotFound, Unauthorized
from werkzeug.utils import redirect

from among_us_friends.blueprints import open_repository
from among_us_friends.repository import SqliteGame, Repository

games = Blueprint('games', __name__)


class Game:
    def __init__(self, repo: Repository, uuid: UUID):
        self._repo = repo
        self._game = repo.game_dao().get_by_uuid(uuid)

    @property
    def owner(self):
        return self._repo.user_dao().get_by_rowid(self._game.owner)

    @property
    def room_id(self):
        return self._game.room_id

    @property
    def room(self):
        return self._repo.room_dao().get_by_rowid(self.room_id)

    @property
    def title(self):
        return self._game.title

    @property
    def uuid(self):
        return self._game.uuid


@games.route('/games/<game_id>')
@login_required
def game(game_id):
    with open_repository() as repo:
        try:
            game = Game(repo, UUID(game_id))
            admin_rights = current_user.uuid == game.owner.uuid
            return render_template('game.html', game=game, admin_rights=admin_rights)
        except ValueError:
            raise NotFound()


@games.route('/games/<game_id>/admin')
@login_required
def game_admin(game_id):
    with open_repository() as repo:
        game = Game(repo, UUID(game_id))
        if current_user.uuid != game.owner.uuid:
            raise Unauthorized()
        return render_template('game_admin.html', game=game)


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
