import sqlite3
from flask import Flask, g

def create_app(test_config=None):
    app = Flask(__name__)
    app.config["DATABASE"] = "cookbook.db"

    if test_config:
        app.config.update(test_config)

    from .routes import main
    app.register_blueprint(main)

    app.teardown_appcontext(close_db)

    return app

def get_db():
    from flask import current_app
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
