from flask import Blueprint, render_template, request
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
