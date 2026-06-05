import pytest
from app import create_app, get_db


@pytest.fixture
def app(tmp_path):
    db_path = str(tmp_path / "test.db")
    application = create_app({"DATABASE": db_path, "TESTING": True})

    with application.app_context():
        db = get_db()
        with open("database/schema.sql") as f:
            db.executescript(f.read())
        db.commit()

    yield application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def seeded(app):
    """Database pre-loaded with one recipe and two ingredients."""
    with app.app_context():
        db = get_db()
        db.execute(
            "INSERT INTO recipes (name, instructions, prep_time, cook_time, servings, tags) "
            "VALUES ('Pancakes', 'Mix and cook.', 5, 10, 4, 'vegetarian')"
        )
        db.execute("INSERT INTO ingredients (name, substitutes) VALUES ('flour', 'almond flour')")
        db.execute("INSERT INTO ingredients (name, substitutes) VALUES ('milk', 'oat milk')")
        db.execute("INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit) VALUES (1, 1, '2', 'cups')")
        db.execute("INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit) VALUES (1, 2, '1', 'cup')")
        db.commit()
    return app
