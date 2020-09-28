from pathlib import Path

from flask import current_app

from among_us_friends.repository import Repository


def open_repository():
    db_path = Path(current_app.config['DB_PATH'])
    schema_path = Path(current_app.config['SCHEMA_PATH'])
    return Repository(db_path, schema_path)
