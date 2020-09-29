from uuid import UUID

from flask import Blueprint, render_template, url_for, request, current_app
from flask_login import current_user, login_required
from werkzeug.utils import redirect

from among_us_friends.blueprints import open_repository


lobbies = Blueprint('lobbies', __name__)


@lobbies.route('/lobbies/create')
def new_lobby():
    return render_template('new_lobby.html')


@lobbies.route('/lobbies/<lobby_id>')
@login_required
def lobby(lobby_id):
    lobby_uuid = UUID(lobby_id)
    with open_repository() as repo:
        lobby = repo.lobby_dao().require_lobby(lobby_uuid)
        rooms = repo.room_dao().list_for_lobby(lobby)
    rooms = list(rooms)
    return render_template('lobby.html', lobby=lobby, rooms=rooms, user=current_user)


@lobbies.route('/lobbies/create', methods=['POST'])
@login_required
def create_lobby():
    form = request.form
    title = form['title']
    anyone = bool(form.get('anyone', 'off') == 'on')
    with open_repository() as repo:
        lobby = repo.lobby_dao().create(title, anyone)
    return redirect(url_for('lobby', lobby_id=lobby.uuid.hex))


@lobbies.route('/lobbies/<lobby_id>/makeRoom')
@login_required
def create_room(lobby_id: str):
    return render_template("new_room.html")


@lobbies.route('/lobbies/<lobby_id>/makeRoom', methods=('POST',))
@login_required
def post_create_room(lobby_id: str):
    form = request.form

    room_title = form['title']

    with open_repository() as repo:
        lobby = repo.lobby_dao().require_lobby(UUID(lobby_id))
        room = repo.room_dao().create(lobby, room_title)
        repo.commit()
    return redirect(url_for('rooms.room', room_id=room.uuid.hex))
