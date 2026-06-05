"""
Tests for the favorites feature:
- Toggling a recipe marks it as a favorite
- Toggling again unmarks it
- The filled star appears on the recipe detail page when favorited
- The index favorites filter shows only favorited recipes
- Non-favorited recipes are excluded from the favorites filter
- Favorites are sorted to the top of the unfiltered index
"""


def test_toggle_favorite_marks_recipe(seeded, client, app):
    """POSTing to the favorite route sets is_favorite to 1."""
    client.post("/recipe/1/favorite")
    with app.app_context():
        from app import get_db
        r = get_db().execute("SELECT is_favorite FROM recipes WHERE id = 1").fetchone()
        assert r["is_favorite"] == 1


def test_toggle_favorite_unmarks_recipe(seeded, client, app):
    """POSTing to the favorite route twice toggles is_favorite back to 0."""
    client.post("/recipe/1/favorite")
    client.post("/recipe/1/favorite")
    with app.app_context():
        from app import get_db
        r = get_db().execute("SELECT is_favorite FROM recipes WHERE id = 1").fetchone()
        assert r["is_favorite"] == 0


def test_favorite_star_shown_on_recipe_page(seeded, client):
    """A favorited recipe shows the filled star (★) on its detail page."""
    client.post("/recipe/1/favorite")
    response = client.get("/recipe/1")
    assert "★".encode() in response.data


def test_unfavorited_shows_empty_star(seeded, client):
    """A recipe that is not favorited shows the empty star (☆) on its detail page."""
    response = client.get("/recipe/1")
    assert "☆".encode() in response.data


def test_favorites_filter_shows_favorited_recipes(seeded, client):
    """/?favorites=1 returns recipes that have been favorited."""
    client.post("/recipe/1/favorite")
    response = client.get("/?favorites=1")
    assert b"Pancakes" in response.data


def test_favorites_filter_excludes_non_favorites(seeded, client, app):
    """/?favorites=1 excludes recipes that have not been favorited."""
    with app.app_context():
        from app import get_db
        db = get_db()
        db.execute("INSERT INTO recipes (name, instructions) VALUES ('Salad', 'Toss.')")
        db.commit()
    response = client.get("/?favorites=1")
    assert b"Pancakes" not in response.data
    assert b"Salad" not in response.data


def test_favorites_sorted_to_top_on_index(seeded, client, app):
    """Favorited recipes appear before non-favorited recipes on the main index."""
    with app.app_context():
        from app import get_db
        db = get_db()
        db.execute("INSERT INTO recipes (name, instructions) VALUES ('Aardvark Stew', 'Cook.')")
        db.commit()
    client.post("/recipe/1/favorite")
    response = client.get("/")
    pancakes_pos = response.data.find(b"Pancakes")
    stew_pos = response.data.find(b"Aardvark Stew")
    assert pancakes_pos < stew_pos
