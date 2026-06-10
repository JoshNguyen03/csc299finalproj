"""
Tests for the persistent pantry and "what can I make?" mode:
- Page loads and shows an empty-pantry message
- Adding an ingredient persists it and shows it on the page
- Duplicate (case-insensitive) additions are ignored
- Removing an item deletes it
- Recipes are shown only once everything they need is in the pantry
- Extra pantry items don't exclude an otherwise-makeable recipe
"""


def test_pantry_page_loads_empty(client):
    """The pantry page returns 200 and shows the empty-pantry message."""
    response = client.get("/pantry")
    assert response.status_code == 200
    assert b"Your pantry is empty" in response.data


def test_add_item_to_pantry(client, app):
    """Adding an ingredient stores it in the pantry_items table."""
    client.post("/pantry/add", data={"name": "flour"})
    with app.app_context():
        from app import get_db
        item = get_db().execute("SELECT * FROM pantry_items WHERE name = 'flour'").fetchone()
        assert item is not None


def test_added_item_appears_on_pantry_page(client):
    """An added ingredient appears in the pantry list."""
    client.post("/pantry/add", data={"name": "flour"})
    response = client.get("/pantry")
    assert b"flour" in response.data
    assert b"Your pantry is empty" not in response.data


def test_duplicate_item_ignored(client, app):
    """Adding the same ingredient again (different case) doesn't create a duplicate."""
    client.post("/pantry/add", data={"name": "flour"})
    client.post("/pantry/add", data={"name": "Flour"})
    with app.app_context():
        from app import get_db
        count = get_db().execute("SELECT COUNT(*) FROM pantry_items").fetchone()[0]
        assert count == 1


def test_remove_item_from_pantry(client, app):
    """Removing a pantry item deletes it from the database."""
    client.post("/pantry/add", data={"name": "flour"})
    with app.app_context():
        from app import get_db
        item = get_db().execute("SELECT id FROM pantry_items WHERE name = 'flour'").fetchone()
        item_id = item["id"]
    client.post(f"/pantry/remove/{item_id}")
    with app.app_context():
        from app import get_db
        gone = get_db().execute("SELECT * FROM pantry_items WHERE id = ?", (item_id,)).fetchone()
        assert gone is None


def test_pantry_full_match_shows_recipe(seeded, client):
    """A recipe shows up once every ingredient it needs is in the pantry."""
    client.post("/pantry/add", data={"name": "flour"})
    client.post("/pantry/add", data={"name": "milk"})
    response = client.get("/pantry")
    assert b"Pancakes" in response.data


def test_pantry_partial_match_excludes_recipe(seeded, client):
    """Missing one required ingredient excludes the recipe from results."""
    client.post("/pantry/add", data={"name": "flour"})
    response = client.get("/pantry")
    assert b"Pancakes" not in response.data
    assert b"No recipes can be made" in response.data


def test_pantry_extra_ingredients_still_match(seeded, client, app):
    """Having extra ingredients beyond what's needed still shows the recipe."""
    with app.app_context():
        from app import get_db
        get_db().execute("INSERT INTO ingredients (name) VALUES ('sugar')")
        get_db().commit()
    client.post("/pantry/add", data={"name": "flour"})
    client.post("/pantry/add", data={"name": "milk"})
    client.post("/pantry/add", data={"name": "sugar"})
    response = client.get("/pantry")
    assert b"Pancakes" in response.data
