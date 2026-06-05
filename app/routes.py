from flask import Blueprint, render_template, request, redirect, url_for
from . import get_db

main = Blueprint("main", __name__)

@main.route("/")
def index():
    db = get_db()
    recipes = db.execute("SELECT * FROM recipes").fetchall()
    return render_template("index.html", recipes=recipes)

@main.route("/recipe/<int:recipe_id>")
def recipe(recipe_id):
    db = get_db()
    recipe = db.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
    ingredients = db.execute(
        "SELECT i.name, ri.quantity, ri.unit FROM ingredients i "
        "JOIN recipe_ingredients ri ON i.id = ri.ingredient_id "
        "WHERE ri.recipe_id = ?", (recipe_id,)
    ).fetchall()
    return render_template("recipe.html", recipe=recipe, ingredients=ingredients)

@main.route("/recipe/new", methods=["GET", "POST"])
def new_recipe():
    if request.method == "POST":
        db = get_db()
        name = request.form["name"]
        instructions = request.form["instructions"]
        prep_time = request.form["prep_time"] or None
        cook_time = request.form["cook_time"] or None
        servings = request.form["servings"] or None
        tags = request.form["tags"]

        cursor = db.execute(
            "INSERT INTO recipes (name, instructions, prep_time, cook_time, servings, tags) VALUES (?, ?, ?, ?, ?, ?)",
            (name, instructions, prep_time, cook_time, servings, tags)
        )
        recipe_id = cursor.lastrowid

        names = request.form.getlist("ingredient_name")
        quantities = request.form.getlist("ingredient_quantity")
        units = request.form.getlist("ingredient_unit")

        for ing_name, qty, unit in zip(names, quantities, units):
            ing_name = ing_name.strip()
            if not ing_name:
                continue
            existing = db.execute("SELECT id FROM ingredients WHERE name = ?", (ing_name,)).fetchone()
            if existing:
                ing_id = existing["id"]
            else:
                ing_cursor = db.execute("INSERT INTO ingredients (name) VALUES (?)", (ing_name,))
                ing_id = ing_cursor.lastrowid
            db.execute(
                "INSERT OR IGNORE INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit) VALUES (?, ?, ?, ?)",
                (recipe_id, ing_id, qty.strip(), unit.strip())
            )

        db.commit()
        return redirect(url_for("main.recipe", recipe_id=recipe_id))

    return render_template("recipe_form.html")

@main.route("/search")
def search():
    db = get_db()
    selected = request.args.getlist("ingredients")
    recipes = []
    if selected:
        placeholders = ",".join("?" * len(selected))
        recipes = db.execute(
            f"SELECT DISTINCT r.* FROM recipes r "
            f"JOIN recipe_ingredients ri ON r.id = ri.recipe_id "
            f"JOIN ingredients i ON i.id = ri.ingredient_id "
            f"WHERE i.name IN ({placeholders})",
            selected
        ).fetchall()
    all_ingredients = db.execute("SELECT name FROM ingredients ORDER BY name").fetchall()
    return render_template("search.html", recipes=recipes, all_ingredients=all_ingredients, selected=selected)
