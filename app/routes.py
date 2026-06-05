from flask import Blueprint, render_template, request, redirect, url_for
from . import get_db

main = Blueprint("main", __name__)


def save_ingredients(db, recipe_id, names, quantities, units, substitutes):
    db.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ?", (recipe_id,))
    for ing_name, qty, unit, subs in zip(names, quantities, units, substitutes):
        ing_name = ing_name.strip()
        if not ing_name:
            continue
        existing = db.execute("SELECT id FROM ingredients WHERE name = ?", (ing_name,)).fetchone()
        if existing:
            ing_id = existing["id"]
            db.execute("UPDATE ingredients SET substitutes = ? WHERE id = ?", (subs.strip() or None, ing_id))
        else:
            cur = db.execute(
                "INSERT INTO ingredients (name, substitutes) VALUES (?, ?)",
                (ing_name, subs.strip() or None)
            )
            ing_id = cur.lastrowid
        db.execute(
            "INSERT OR IGNORE INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit) VALUES (?, ?, ?, ?)",
            (recipe_id, ing_id, qty.strip(), unit.strip())
        )


@main.route("/")
def index():
    db = get_db()
    recipes = db.execute("SELECT * FROM recipes").fetchall()
    return render_template("index.html", recipes=recipes)


@main.route("/recipe/new", methods=["GET", "POST"])
def new_recipe():
    if request.method == "POST":
        db = get_db()
        cur = db.execute(
            "INSERT INTO recipes (name, instructions, prep_time, cook_time, servings, tags) VALUES (?, ?, ?, ?, ?, ?)",
            (
                request.form["name"],
                request.form["instructions"],
                request.form["prep_time"] or None,
                request.form["cook_time"] or None,
                request.form["servings"] or None,
                request.form["tags"],
            )
        )
        recipe_id = cur.lastrowid
        save_ingredients(db, recipe_id,
            request.form.getlist("ingredient_name"),
            request.form.getlist("ingredient_quantity"),
            request.form.getlist("ingredient_unit"),
            request.form.getlist("ingredient_substitutes"),
        )
        db.commit()
        return redirect(url_for("main.recipe", recipe_id=recipe_id))
    return render_template("recipe_form.html", recipe=None, ingredients=[])


@main.route("/recipe/<int:recipe_id>")
def recipe(recipe_id):
    db = get_db()
    r = db.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
    ingredients = db.execute(
        "SELECT i.name, i.substitutes, ri.quantity, ri.unit FROM ingredients i "
        "JOIN recipe_ingredients ri ON i.id = ri.ingredient_id "
        "WHERE ri.recipe_id = ?", (recipe_id,)
    ).fetchall()
    return render_template("recipe.html", recipe=r, ingredients=ingredients)


@main.route("/recipe/<int:recipe_id>/edit", methods=["GET", "POST"])
def edit_recipe(recipe_id):
    db = get_db()
    if request.method == "POST":
        db.execute(
            "UPDATE recipes SET name=?, instructions=?, prep_time=?, cook_time=?, servings=?, tags=? WHERE id=?",
            (
                request.form["name"],
                request.form["instructions"],
                request.form["prep_time"] or None,
                request.form["cook_time"] or None,
                request.form["servings"] or None,
                request.form["tags"],
                recipe_id,
            )
        )
        save_ingredients(db, recipe_id,
            request.form.getlist("ingredient_name"),
            request.form.getlist("ingredient_quantity"),
            request.form.getlist("ingredient_unit"),
            request.form.getlist("ingredient_substitutes"),
        )
        db.commit()
        return redirect(url_for("main.recipe", recipe_id=recipe_id))

    r = db.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
    ingredients = db.execute(
        "SELECT i.name, i.substitutes, ri.quantity, ri.unit FROM ingredients i "
        "JOIN recipe_ingredients ri ON i.id = ri.ingredient_id "
        "WHERE ri.recipe_id = ?", (recipe_id,)
    ).fetchall()
    return render_template("recipe_form.html", recipe=r, ingredients=ingredients)


@main.route("/recipe/<int:recipe_id>/delete", methods=["POST"])
def delete_recipe(recipe_id):
    db = get_db()
    db.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ?", (recipe_id,))
    db.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
    db.commit()
    return redirect(url_for("main.index"))


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
