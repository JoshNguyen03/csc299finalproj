"""
Tests for the meal planner and shopping list:
- Plan page loads
- Adding a recipe to a day persists it
- Removing an entry deletes it
- Invalid day names are silently ignored
- Shopping list aggregates quantities for the same ingredient
- Shopping list handles non-numeric quantities
- Shopping list shows empty state when plan is empty
"""


def test_plan_page_loads(seeded, client):
    """The meal plan page returns 200 and shows all seven days."""
    response = client.get("/plan")
    assert response.status_code == 200
    assert b"Monday" in response.data
    assert b"Sunday" in response.data


def test_add_recipe_to_plan(seeded, client, app):
    """Adding a recipe to a day stores it in the meal_plan table."""
    client.post("/plan/add", data={"recipe_id": "1", "day": "Monday"})
    with app.app_context():
        from app import get_db
        entry = get_db().execute(
            "SELECT * FROM meal_plan WHERE recipe_id = 1 AND day = 'Monday'"
        ).fetchone()
        assert entry is not None


def test_added_recipe_appears_on_plan_page(seeded, client):
    """A recipe added to the plan appears on the meal plan page."""
    client.post("/plan/add", data={"recipe_id": "1", "day": "Wednesday"})
    response = client.get("/plan")
    assert b"Pancakes" in response.data


def test_remove_recipe_from_plan(seeded, client, app):
    """Removing a plan entry deletes it from the database."""
    client.post("/plan/add", data={"recipe_id": "1", "day": "Tuesday"})
    with app.app_context():
        from app import get_db
        entry = get_db().execute("SELECT id FROM meal_plan").fetchone()
        entry_id = entry["id"]
    client.post(f"/plan/remove/{entry_id}")
    with app.app_context():
        from app import get_db
        gone = get_db().execute("SELECT * FROM meal_plan WHERE id = ?", (entry_id,)).fetchone()
        assert gone is None


def test_invalid_day_is_ignored(seeded, client, app):
    """A POST with an invalid day name does not insert any row."""
    client.post("/plan/add", data={"recipe_id": "1", "day": "Funday"})
    with app.app_context():
        from app import get_db
        count = get_db().execute("SELECT COUNT(*) FROM meal_plan").fetchone()[0]
        assert count == 0


def test_shopping_list_empty_state(client):
    """The shopping list page loads and shows an empty-state message when the plan is empty."""
    response = client.get("/plan/shopping-list")
    assert response.status_code == 200
    assert b"empty" in response.data


def test_shopping_list_shows_ingredients(seeded, client):
    """Ingredients from planned recipes appear on the shopping list."""
    client.post("/plan/add", data={"recipe_id": "1", "day": "Monday"})
    response = client.get("/plan/shopping-list")
    assert b"flour" in response.data
    assert b"milk" in response.data


def test_shopping_list_sums_quantities(seeded, client):
    """The same recipe planned twice doubles the ingredient quantities."""
    client.post("/plan/add", data={"recipe_id": "1", "day": "Monday"})
    client.post("/plan/add", data={"recipe_id": "1", "day": "Thursday"})
    response = client.get("/plan/shopping-list")
    # flour: 2 cups * 2 = 4 cups
    assert b"4" in response.data


def test_shopping_list_non_numeric_quantity(seeded, client, app):
    """Non-numeric quantities like 'to taste' appear unchanged on the shopping list."""
    with app.app_context():
        from app import get_db
        db = get_db()
        db.execute("INSERT INTO ingredients (name) VALUES ('salt')")
        db.execute(
            "INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit) "
            "VALUES (1, 3, 'to taste', '')"
        )
        db.commit()
    client.post("/plan/add", data={"recipe_id": "1", "day": "Monday"})
    response = client.get("/plan/shopping-list")
    assert b"to taste" in response.data
