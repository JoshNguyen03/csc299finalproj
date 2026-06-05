"""
Tests for recipe features:
- Browsing recipes
- Viewing a recipe
- Creating a recipe
- Editing a recipe
- Deleting a recipe
"""


def test_home_shows_all_recipes(seeded, client):
    """The home page lists every recipe by name."""
    response = client.get("/")
    assert b"Pancakes" in response.data


def test_home_empty_state(client):
    """The home page handles having no recipes gracefully."""
    response = client.get("/")
    assert response.status_code == 200


def test_view_recipe_shows_details(seeded, client):
    """A recipe page shows the name, ingredients, and instructions."""
    response = client.get("/recipe/1")
    assert b"Pancakes" in response.data
    assert b"flour" in response.data
    assert b"Mix and cook." in response.data


def test_view_recipe_shows_meta(seeded, client):
    """A recipe page shows prep time, cook time, and servings."""
    response = client.get("/recipe/1")
    assert b"5" in response.data   # prep time
    assert b"10" in response.data  # cook time
    assert b"4" in response.data   # servings


def test_create_recipe_saves_to_db(client, app):
    """Submitting the new recipe form creates a recipe in the database."""
    client.post("/recipe/new", data={
        "name": "Omelette",
        "instructions": "Beat eggs, cook in pan.",
        "prep_time": "2",
        "cook_time": "5",
        "servings": "1",
        "tags": "",
        "ingredient_name": ["eggs"],
        "ingredient_quantity": ["3"],
        "ingredient_unit": ["whole"],
        "ingredient_substitutes": [""],
    })

    with app.app_context():
        from app import get_db
        recipe = get_db().execute("SELECT * FROM recipes WHERE name = 'Omelette'").fetchone()
        assert recipe is not None
        assert recipe["instructions"] == "Beat eggs, cook in pan."


def test_create_recipe_redirects_to_recipe_page(client):
    """After creating a recipe the user is sent to the recipe detail page."""
    response = client.post("/recipe/new", data={
        "name": "Toast",
        "instructions": "Toast bread.",
        "prep_time": "", "cook_time": "", "servings": "", "tags": "",
        "ingredient_name": [], "ingredient_quantity": [],
        "ingredient_unit": [], "ingredient_substitutes": [],
    }, follow_redirects=False)
    assert response.status_code == 302
    assert "/recipe/" in response.headers["Location"]


def test_create_recipe_skips_blank_ingredient_rows(client, app):
    """Blank ingredient rows in the form are ignored and not saved."""
    client.post("/recipe/new", data={
        "name": "Simple Dish",
        "instructions": "Cook it.",
        "prep_time": "", "cook_time": "", "servings": "", "tags": "",
        "ingredient_name": ["rice", ""],
        "ingredient_quantity": ["1", ""],
        "ingredient_unit": ["cup", ""],
        "ingredient_substitutes": ["", ""],
    })

    with app.app_context():
        from app import get_db
        count = get_db().execute("SELECT COUNT(*) FROM recipe_ingredients").fetchone()[0]
        assert count == 1


def test_edit_recipe_updates_fields(seeded, client, app):
    """Editing a recipe changes its stored name and instructions."""
    client.post("/recipe/1/edit", data={
        "name": "Fluffy Pancakes",
        "instructions": "Whisk well, cook on medium heat.",
        "prep_time": "5", "cook_time": "10", "servings": "4", "tags": "vegetarian",
        "ingredient_name": ["flour"],
        "ingredient_quantity": ["2"],
        "ingredient_unit": ["cups"],
        "ingredient_substitutes": ["almond flour"],
    })

    with app.app_context():
        from app import get_db
        recipe = get_db().execute("SELECT * FROM recipes WHERE id = 1").fetchone()
        assert recipe["name"] == "Fluffy Pancakes"
        assert recipe["instructions"] == "Whisk well, cook on medium heat."


def test_edit_recipe_redirects_to_recipe_page(seeded, client):
    """After editing, the user is sent back to the recipe detail page."""
    response = client.post("/recipe/1/edit", data={
        "name": "Pancakes", "instructions": "Mix and cook.",
        "prep_time": "5", "cook_time": "10", "servings": "4", "tags": "vegetarian",
        "ingredient_name": ["flour"], "ingredient_quantity": ["2"],
        "ingredient_unit": ["cups"], "ingredient_substitutes": ["almond flour"],
    }, follow_redirects=False)
    assert response.status_code == 302
    assert "/recipe/1" in response.headers["Location"]


def test_delete_recipe_removes_it(seeded, client, app):
    """Deleting a recipe removes it from the database entirely."""
    client.post("/recipe/1/delete")

    with app.app_context():
        from app import get_db
        recipe = get_db().execute("SELECT * FROM recipes WHERE id = 1").fetchone()
        assert recipe is None


def test_delete_recipe_removes_its_ingredients(seeded, client, app):
    """Deleting a recipe also removes its ingredient associations."""
    client.post("/recipe/1/delete")

    with app.app_context():
        from app import get_db
        links = get_db().execute("SELECT * FROM recipe_ingredients WHERE recipe_id = 1").fetchall()
        assert len(links) == 0


def test_delete_recipe_redirects_home(seeded, client):
    """After deletion the user is sent back to the home page."""
    response = client.post("/recipe/1/delete", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"] == "/"


def test_recipe_default_shows_original_servings(seeded, client):
    """Without a ?servings param the form input shows the recipe's original serving count."""
    response = client.get("/recipe/1")
    assert b'value="4"' in response.data


def test_recipe_scales_quantities_up(seeded, client):
    """Requesting double the servings doubles numeric ingredient quantities."""
    response = client.get("/recipe/1?servings=8")
    assert b"4 cups" in response.data   # flour: 2 cups * 2 = 4 cups


def test_recipe_scales_quantities_down(seeded, client):
    """Requesting half the servings halves numeric ingredient quantities."""
    response = client.get("/recipe/1?servings=2")
    assert b"1 cups" in response.data   # flour: 2 cups / 2 = 1 cup
    assert b"1/2" in response.data      # milk: 1 cup / 2 = 1/2


def test_recipe_non_numeric_quantity_unchanged(seeded, client, app):
    """Non-numeric quantities such as 'to taste' are left unchanged when scaling."""
    with app.app_context():
        from app import get_db
        db = get_db()
        db.execute("INSERT INTO ingredients (name) VALUES ('salt')")
        db.execute(
            "INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit) "
            "VALUES (1, 3, 'to taste', '')"
        )
        db.commit()
    response = client.get("/recipe/1?servings=8")
    assert b"to taste" in response.data
