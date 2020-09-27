import logging
from pathlib import Path
from uuid import UUID, uuid4

from flask import Flask, render_template, request, json, url_for
from flask_login import LoginManager, login_required, current_user, logout_user, login_user
from werkzeug.exceptions import abort
from werkzeug.utils import redirect

from among_us_friends.color_stats import ColorsMatchesStats
from among_us_friends.imposter_stat import HtmlImposterStatsFormatter
from among_us_friends.player_stats import PlayersMatchesStats
from among_us_friends.repository import Repository, NotFoundException

DB_PATH = Path('server/db.sqlite')
SCHEMA_PATH = Path("server/schema.sql")
CONFIG_PATH = Path("server/config.cfg")


if not CONFIG_PATH.exists():
    with open(CONFIG_PATH, 'w') as fp:
        fp.write('SECRET_KEY = \'' + uuid4().hex + '\'')


app = Flask('among-us-friends')
app.config.from_pyfile(CONFIG_PATH)

login = LoginManager(app)
login.login_view = '/login'


@login.user_loader
def load_user(uuid: str):
    uuid = UUID(uuid)
    with open_repo() as repo:
        return repo.user_dao().require_user(uuid)


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()


def open_repo():
    return Repository(DB_PATH, SCHEMA_PATH)


@app.route('/')
def index():
    with open_repo() as repo:
        lobbies = repo.lobby_dao().list()
    return render_template("index.html", lobbies=lobbies)


@app.route("/admin/users")
@login_required
def admin_users():
    with open_repo() as repo:
        users = repo.user_dao().list()
    return json.dumps(users)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'GET':
        return render_template('login.html')
    try:
        form = request.form
        print(form)
        with open_repo() as repo:
            user = repo.user_dao().require_user(form['username'])
        login_user(user, form['remember'])
    except Exception as e:
        logger.exception(e)
        return render_template('login.html')


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/dump")
def dump():
    with open_repo() as repo:
        return '<pre>' + '\n'.join(repo._conn.iterdump())


@app.route('/lobbies/create')
def new_lobby():
    return render_template('new_lobby.html')


@app.route('/lobbies/create', methods=['POST'])
def create_lobby():
    form = request.form
    title = form['title']
    anyone = bool(form.get('anyone', 'off') == 'on')
    with open_repo() as repo:
        lobby = repo.lobby_dao().create(title, anyone)
    return redirect(url_for('lobby', lobby_id=lobby.uuid.hex))


@app.route('/lobbies/<lobby_id>')
def lobby(lobby_id):
    lobby_uuid = UUID(lobby_id)
    with open_repo() as repo:
        lobby = repo.lobby_dao().require_lobby(lobby_uuid)
        rooms = repo.room_dao().list_for_lobby(lobby)
    rooms = list(rooms)
    return render_template('lobby.html', lobby=lobby, rooms=rooms)


@app.route('/createRoom')
def show_create_room():
    return render_template("new_room.html")


@app.route('/createRoom', methods=('POST',))
def post_create_room():
    form = request.form

    room_title = form['title']

    with open_repo() as repo:
        room = repo.room_dao().create(room_title)
    return redirect(url_for('room', room_id=room.uuid.hex))


@app.route("/rooms/<room_id>")
def room(room_id):
    room_uuid = UUID(room_id)
    with open_repo() as repo:
        try:
            room = repo.room_dao().require_room(room_uuid)
        except NotFoundException:
            abort(404)
        matches = list(repo.match_dao().list_for_room(room))
        lobby_id = repo.lobby_dao().get_by_rowid(room.lobby).uuid.hex
        counts = repo.result_dao().counts_by_match_rowid_for_room(room)
        player_stats = list(PlayersMatchesStats(matches).using(repo))
        color_stats = list(ColorsMatchesStats(matches).using(repo))
    counts = dict(counts)
    matches = {m.rowid: m for m in matches}
    match_counts = ((matches.get(k, None), counts.get(k, None)) for k in counts.keys() | matches.keys())
    return render_template("room.html",
                           room=room,
                           match_counts=match_counts,
                           lobby=lobby_id,
                           player_stats=HtmlImposterStatsFormatter(player_stats),
                           color_stats=HtmlImposterStatsFormatter(color_stats))


if __name__ == '__main__':
    app.run(debug=True)
