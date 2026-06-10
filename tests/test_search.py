"""
Tests for the ingredient search feature:
- Recipes are found when a matching ingredient is selected
- Recipes with none of the selected ingredients are excluded
- Selecting no ingredients returns no results
- A recipe is not listed twice when it matches multiple selected ingredients
"""


def test_search_finds_recipe_by_ingredient(seeded, client):
    """Selecting an ingredient that belongs to a recipe returns that recipe."""
    response = client.get("/search?ingredients=flour")
    assert b"Pancakes" in response.data


def test_search_excludes_non_matching_recipes(seeded, client, app):
    """Recipes that don't contain any selected ingredient are not shown."""
    with app.app_context():
        from app import get_db
        db = get_db()
        db.execute("INSERT INTO recipes (name, instructions) VALUES ('Salad', 'Toss.')")
        db.execute("INSERT INTO ingredients (name) VALUES ('lettuce')")
        db.execute("INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit) VALUES (2, 3, '1', 'head')")
        db.commit()

    response = client.get("/search?ingredients=flour")
    assert b"Pancakes" in response.data
    assert b"Salad" not in response.data


def test_search_with_no_ingredients_selected_returns_no_results(seeded, client):
    """Submitting the search form with nothing selected shows no recipes."""
    response = client.get("/search")
    assert b"Pancakes" not in response.data


def test_search_does_not_duplicate_results(seeded, client):
    """A recipe matching multiple selected ingredients appears only once."""
    response = client.get("/search?ingredients=flour&ingredients=milk")
    assert response.data.count(b"Pancakes") == 1


def test_search_page_lists_all_available_ingredients(seeded, client):
    """The search page shows all ingredients as selectable options."""
    response = client.get("/search")
    assert b"flour" in response.data
    assert b"milk" in response.data


def test_search_finds_recipe_by_tag(seeded, client):
    """Selecting a tag that belongs to a recipe returns that recipe."""
    response = client.get("/search?tags=vegetarian")
    assert b"Pancakes" in response.data


def test_search_tag_excludes_non_matching_recipes(seeded, client, app):
    """Recipes that don't have the selected tag are excluded."""
    with app.app_context():
        from app import get_db
        db = get_db()
        db.execute("INSERT INTO recipes (name, instructions, tags) VALUES ('Steak', 'Grill.', 'meat')")
        db.commit()

    response = client.get("/search?tags=vegetarian")
    assert b"Pancakes" in response.data
    assert b"Steak" not in response.data


def test_search_tag_and_ingredient_combined(seeded, client):
    """Both tag and ingredient filters must be satisfied."""
    response = client.get("/search?tags=vegetarian&ingredients=flour")
    assert b"Pancakes" in response.data


def test_search_tag_and_ingredient_no_overlap(seeded, client, app):
    """A recipe matching the tag but not the ingredient is excluded when both filters are active."""
    with app.app_context():
        from app import get_db
        db = get_db()
        db.execute("INSERT INTO recipes (name, instructions, tags) VALUES ('Oatmeal', 'Cook oats.', 'vegetarian')")
        db.execute("INSERT INTO ingredients (name) VALUES ('oats')")
        db.execute("INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit) VALUES (2, 3, '1', 'cup')")
        db.commit()

    response = client.get("/search?tags=vegetarian&ingredients=flour")
    assert b"Pancakes" in response.data
    assert b"Oatmeal" not in response.data


def test_search_page_lists_all_available_tags(seeded, client):
    """The search page shows all tags as selectable options."""
    response = client.get("/search")
    assert b"vegetarian" in response.data


def test_search_finds_recipe_by_name(seeded, client):
    """A text query matching the recipe name returns that recipe, case-insensitively."""
    response = client.get("/search?q=pancake")
    assert b"Pancakes" in response.data


def test_search_finds_recipe_by_instructions(seeded, client):
    """A text query matching the instructions returns that recipe."""
    response = client.get("/search?q=mix")
    assert b"Pancakes" in response.data


def test_search_text_excludes_non_matching_recipes(seeded, client, app):
    """A text query that doesn't match a recipe's name or instructions excludes it."""
    with app.app_context():
        from app import get_db
        db = get_db()
        db.execute("INSERT INTO recipes (name, instructions) VALUES ('Salad', 'Toss the greens.')")
        db.commit()

    response = client.get("/search?q=pancake")
    assert b"Pancakes" in response.data
    assert b"Salad" not in response.data


def test_search_text_with_no_match_shows_message(seeded, client):
    """A text query with no matches shows the no-results message."""
    response = client.get("/search?q=lasagna")
    assert b"Pancakes" not in response.data
    assert b"No recipes found matching those filters." in response.data


def test_search_text_and_tag_combined(seeded, client):
    """A text query and a tag filter must both be satisfied."""
    response = client.get("/search?q=pancake&tags=vegetarian")
    assert b"Pancakes" in response.data
