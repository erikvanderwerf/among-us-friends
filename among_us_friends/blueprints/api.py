from flask import Blueprint, request, Response
from werkzeug.exceptions import BadRequest

from among_us_friends.blueprints import open_repository

api = Blueprint('api', __name__)


class LiveGamesHtmlFormatter:
    pass


# @api.route('/api/rooms/<room_id>/games')
# def live_room_games(room_id):
#     known_accept = {
#         'text/html': LiveGamesHtmlFormatter
#     }
#     try:
#         formatter = known_accept[request.headers['Accept']]()
#     except KeyError as e:
#         raise BadRequest('api cannot handle given Accept header.')
#
#     with open_repository() as repo:
#         pass
#
#     return Response(
#         formatter.format(live_games),
#         status=200,
#         headers={
#             'Etag': live_games.etag
#         },
#         mimetype=formatter.mimetype
#     )
