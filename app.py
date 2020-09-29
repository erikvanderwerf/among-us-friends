import logging
from pathlib import Path
from uuid import UUID, uuid4

from flask import Flask, render_template, request, json, url_for, session
from flask_login import LoginManager, login_required, current_user, logout_user, login_user, UserMixin
from werkzeug.utils import redirect

from among_us_friends.blueprints import open_repository
from among_us_friends.blueprints.api import api
from among_us_friends.blueprints.games import games
from among_us_friends.blueprints.lobbies import lobbies
from among_us_friends.blueprints.rooms import rooms
from among_us_friends.repository import SqliteUser, NotFoundException

DB_PATH = Path('server/db.sqlite')
SCHEMA_PATH = Path("server/schema.sql")
CONFIG_PATH = Path("server/config.cfg")


if not CONFIG_PATH.exists():
    with open(CONFIG_PATH, 'w') as fp:
        fp.write(f'SECRET_KEY = \'{uuid4().hex}\'\n'
                 f'DB_PATH = \'{DB_PATH}\'\n'
                 f'SCHEMA_PATH = \'{SCHEMA_PATH}\'\n')


app = Flask('among-us-friends')
app.config.from_pyfile(CONFIG_PATH)

login = LoginManager(app)
login.login_view = '/login'


class UserWrap:
    def __init__(self, user: SqliteUser):
        self._user = user

    @property
    def is_active(self):
        return True

    @property
    def is_authenticated(self):
        return True

    def get_id(self):
        return self._user.uuid.hex

    @property
    def uuid(self):
        return self._user.uuid

    @property
    def username(self):
        return self._user.username


@login.user_loader
def load_user(uuid: str):
    uuid = UUID(uuid)
    with open_repository() as repo:
        try:
            return UserWrap(repo.user_dao().require_uuid(uuid))
        except NotFoundException:
            return None


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()


app.register_blueprint(api)
app.register_blueprint(lobbies)
app.register_blueprint(rooms)
app.register_blueprint(games)


@app.route('/')
def index():
    with open_repository() as repo:
        lobbies = repo.lobby_dao().list()
    return render_template("index.html", lobbies=lobbies)


@app.route("/admin/users")
@login_required
def admin_users():
    with open_repository() as repo:
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
        with open_repository() as repo:
            user = repo.user_dao().require_username(form['username'])
        user = UserWrap(user)
        login_user(user, form.get('remember', False))
    except Exception as e:
        logger.exception(e)
        return render_template('login.html')
    next_url = request.args.get('next', '/')
    return redirect(next_url)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/dump")
def dump():
    with open_repository() as repo:
        return '<pre>' + '\n'.join(repo._conn.iterdump())


@app.route('/users')
def users():
    ret = '<ul>'
    with open_repository() as repo:
        for user in repo.user_dao().list():
            ret += f'<li>{user.username}</li>'
    ret += '</ul>'
    return ret


if __name__ == '__main__':
    app.run(debug=True)
