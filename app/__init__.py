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

    with app.app_context():
        _migrate_db()

    return app


def _migrate_db():
    import os
    db = get_db()
    table = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='recipes'"
    ).fetchone()
    if not table:
        schema = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
        with open(schema) as f:
            db.executescript(f.read())
        return
    columns = [row[1] for row in db.execute("PRAGMA table_info(recipes)").fetchall()]
    if "is_favorite" not in columns:
        db.execute("ALTER TABLE recipes ADD COLUMN is_favorite INTEGER NOT NULL DEFAULT 0")
        db.commit()
    plan_table = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='meal_plan'"
    ).fetchone()
    if not plan_table:
        db.execute(
            "CREATE TABLE meal_plan ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "recipe_id INTEGER NOT NULL, "
            "day TEXT NOT NULL, "
            "FOREIGN KEY (recipe_id) REFERENCES recipes(id))"
        )
        db.commit()
    pantry_table = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='pantry_items'"
    ).fetchone()
    if not pantry_table:
        db.execute(
            "CREATE TABLE pantry_items ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "name TEXT NOT NULL UNIQUE)"
        )
        db.commit()

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
