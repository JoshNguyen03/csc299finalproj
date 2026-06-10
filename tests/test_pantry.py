"""
Tests for pantry mode ("what can I make?"):
- Page loads and lists ingredients
- Selecting all of a recipe's ingredients shows that recipe
- Selecting only some of a recipe's ingredients excludes it
- Selecting a recipe's ingredients plus extras still shows it
- No selection shows no results
"""


def test_pantry_page_loads(seeded, client):
    """The pantry page returns 200 and lists ingredients to choose from."""
    response = client.get("/pantry")
    assert response.status_code == 200
    assert b"flour" in response.data
    assert b"milk" in response.data


def test_pantry_full_match_shows_recipe(seeded, client):
    """Selecting every ingredient a recipe needs shows it as makeable."""
    response = client.get("/pantry?ingredients=flour&ingredients=milk")
    assert b"Pancakes" in response.data


def test_pantry_partial_match_excludes_recipe(seeded, client):
    """Missing one required ingredient excludes the recipe from results."""
    response = client.get("/pantry?ingredients=flour")
    assert b"Pancakes" not in response.data
    assert b"No recipes can be made" in response.data


def test_pantry_extra_ingredients_still_match(seeded, client, app):
    """Having extra ingredients beyond what's needed still shows the recipe."""
    with app.app_context():
        from app import get_db
        get_db().execute("INSERT INTO ingredients (name) VALUES ('sugar')")
        get_db().commit()
    response = client.get("/pantry?ingredients=flour&ingredients=milk&ingredients=sugar")
    assert b"Pancakes" in response.data


def test_pantry_no_selection_shows_no_results(seeded, client):
    """With nothing selected, no recipes are shown and no error message appears."""
    response = client.get("/pantry")
    assert b"Pancakes" not in response.data
    assert b"No recipes can be made" not in response.data
