"""
Tests for ingredient and substitution features:
- Substitutes displayed on recipe page
- Substitutes can be updated
- Substitutes can be cleared
- Ingredients are reused across recipes, not duplicated
"""


def test_substitutes_shown_on_recipe_page(seeded, client):
    """Ingredient substitutes are visible on the recipe detail page."""
    response = client.get("/recipe/1")
    assert b"almond flour" in response.data
    assert b"oat milk" in response.data


def test_substitutes_not_shown_when_absent(client):
    """No substitution text appears for ingredients with no substitutes set."""
    client.post("/recipe/new", data={
        "name": "Plain Rice",
        "instructions": "Boil water, add rice.",
        "prep_time": "", "cook_time": "", "servings": "", "tags": "",
        "ingredient_name": ["rice"],
        "ingredient_quantity": ["1"],
        "ingredient_unit": ["cup"],
        "ingredient_substitutes": [""],
    })
    response = client.get("/recipe/1")
    assert b"substitutes" not in response.data


def test_editing_substitutes_updates_them(seeded, client, app):
    """Changing the substitutes field on edit saves the new value."""
    client.post("/recipe/1/edit", data={
        "name": "Pancakes", "instructions": "Mix and cook.",
        "prep_time": "5", "cook_time": "10", "servings": "4", "tags": "vegetarian",
        "ingredient_name": ["flour"],
        "ingredient_quantity": ["2"],
        "ingredient_unit": ["cups"],
        "ingredient_substitutes": ["oat flour"],
    })

    with app.app_context():
        from app import get_db
        ing = get_db().execute("SELECT substitutes FROM ingredients WHERE name = 'flour'").fetchone()
        assert ing["substitutes"] == "oat flour"


def test_clearing_substitutes_removes_them(seeded, client, app):
    """Clearing the substitutes field and saving removes the stored substitutes."""
    client.post("/recipe/1/edit", data={
        "name": "Pancakes", "instructions": "Mix and cook.",
        "prep_time": "5", "cook_time": "10", "servings": "4", "tags": "vegetarian",
        "ingredient_name": ["flour"],
        "ingredient_quantity": ["2"],
        "ingredient_unit": ["cups"],
        "ingredient_substitutes": [""],
    })

    with app.app_context():
        from app import get_db
        ing = get_db().execute("SELECT substitutes FROM ingredients WHERE name = 'flour'").fetchone()
        assert ing["substitutes"] is None


def test_same_ingredient_not_duplicated_across_recipes(client, app):
    """Adding the same ingredient to two recipes reuses one ingredient row."""
    for name in ("Pasta Bake", "Garlic Bread"):
        client.post("/recipe/new", data={
            "name": name, "instructions": "Cook.", "prep_time": "",
            "cook_time": "", "servings": "", "tags": "",
            "ingredient_name": ["garlic"],
            "ingredient_quantity": ["2"],
            "ingredient_unit": ["cloves"],
            "ingredient_substitutes": [""],
        })

    with app.app_context():
        from app import get_db
        count = get_db().execute("SELECT COUNT(*) FROM ingredients WHERE name = 'garlic'").fetchone()[0]
        assert count == 1
