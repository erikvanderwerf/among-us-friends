from uuid import UUID

from flask import Blueprint, render_template, url_for

from among_us_friends.blueprints import open_repository

users = Blueprint('users', __name__)


@users.route('/users')
def all_users():
    ret = '<ul>'
    with open_repository() as repo:
        for user in repo.user_dao().list():
            ret += f'<li><a href={url_for("users.user", user_id=user.uuid.hex)}>{user.username}</a></li>'
    ret += '</ul>'
    return ret


@users.route('/users/<user_id>')
def user(user_id):
    with open_repository() as repo:
        user = repo.user_dao().require_uuid(UUID(user_id))
    return render_template('user.html', user=user)
