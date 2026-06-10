from collections import defaultdict
from fractions import Fraction
from flask import Blueprint, render_template, request, redirect, url_for
from . import get_db

main = Blueprint("main", __name__)

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _parse_quantity(s):
    """Return a float for a quantity string, or None if it can't be parsed."""
    s = (s or "").strip()
    if not s:
        return None
    try:
        parts = s.split()
        if len(parts) == 2:
            return float(Fraction(parts[0])) + float(Fraction(parts[1]))
        return float(Fraction(s))
    except (ValueError, ZeroDivisionError):
        return None


def _format_quantity(value):
    """Format a float as a readable fraction/mixed-number string."""
    frac = Fraction(value).limit_denominator(16)
    if frac.denominator == 1:
        return str(frac.numerator)
    whole = frac.numerator // frac.denominator
    remainder = frac.numerator % frac.denominator
    if whole:
        return f"{whole} {remainder}/{frac.denominator}"
    return f"{frac.numerator}/{frac.denominator}"


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
    favorites_only = request.args.get("favorites") == "1"
    if favorites_only:
        recipes = db.execute("SELECT * FROM recipes WHERE is_favorite = 1").fetchall()
    else:
        recipes = db.execute("SELECT * FROM recipes ORDER BY is_favorite DESC, name").fetchall()
    return render_template("index.html", recipes=recipes, favorites_only=favorites_only)


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
    rows = db.execute(
        "SELECT i.name, i.substitutes, ri.quantity, ri.unit FROM ingredients i "
        "JOIN recipe_ingredients ri ON i.id = ri.ingredient_id "
        "WHERE ri.recipe_id = ?", (recipe_id,)
    ).fetchall()

    requested = request.args.get("servings", type=int)
    original = r["servings"]
    display_servings = requested if (requested and requested > 0) else original

    ingredients = []
    for row in rows:
        ing = dict(row)
        if requested and requested > 0 and original and original > 0 and requested != original:
            parsed = _parse_quantity(ing["quantity"])
            if parsed is not None:
                ing["quantity"] = _format_quantity(parsed * requested / original)
        ingredients.append(ing)

    return render_template("recipe.html", recipe=r, ingredients=ingredients, display_servings=display_servings)


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


@main.route("/recipe/<int:recipe_id>/favorite", methods=["POST"])
def toggle_favorite(recipe_id):
    db = get_db()
    row = db.execute("SELECT is_favorite FROM recipes WHERE id = ?", (recipe_id,)).fetchone()
    if row:
        db.execute("UPDATE recipes SET is_favorite = ? WHERE id = ?",
                   (0 if row["is_favorite"] else 1, recipe_id))
        db.commit()
    return redirect(url_for("main.recipe", recipe_id=recipe_id))


@main.route("/recipe/<int:recipe_id>/delete", methods=["POST"])
def delete_recipe(recipe_id):
    db = get_db()
    db.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ?", (recipe_id,))
    db.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
    db.commit()
    return redirect(url_for("main.index"))


@main.route("/measurements")
def measurements():
    return render_template("measurements.html")


@main.route("/plan")
def plan():
    db = get_db()
    all_recipes = db.execute("SELECT id, name FROM recipes ORDER BY name").fetchall()
    entries = db.execute(
        "SELECT mp.id, mp.day, r.name AS recipe_name, r.id AS recipe_id "
        "FROM meal_plan mp JOIN recipes r ON mp.recipe_id = r.id"
    ).fetchall()
    plan_by_day = {day: [] for day in DAYS}
    for entry in entries:
        if entry["day"] in plan_by_day:
            plan_by_day[entry["day"]].append(entry)
    return render_template("meal_plan.html", plan_by_day=plan_by_day, days=DAYS, all_recipes=all_recipes)


@main.route("/plan/add", methods=["POST"])
def plan_add():
    db = get_db()
    recipe_id = request.form.get("recipe_id", type=int)
    day = request.form.get("day")
    if recipe_id and day in DAYS:
        db.execute("INSERT INTO meal_plan (recipe_id, day) VALUES (?, ?)", (recipe_id, day))
        db.commit()
    return redirect(url_for("main.plan"))


@main.route("/plan/remove/<int:entry_id>", methods=["POST"])
def plan_remove(entry_id):
    db = get_db()
    db.execute("DELETE FROM meal_plan WHERE id = ?", (entry_id,))
    db.commit()
    return redirect(url_for("main.plan"))


@main.route("/plan/shopping-list")
def shopping_list():
    db = get_db()
    rows = db.execute(
        "SELECT i.name, ri.quantity, ri.unit "
        "FROM meal_plan mp "
        "JOIN recipe_ingredients ri ON mp.recipe_id = ri.recipe_id "
        "JOIN ingredients i ON ri.ingredient_id = i.id"
    ).fetchall()

    totals = defaultdict(lambda: {"numeric": 0.0, "non_numeric": [], "has_numeric": False})
    for row in rows:
        key = (row["name"], row["unit"])
        parsed = _parse_quantity(row["quantity"])
        if parsed is not None:
            totals[key]["numeric"] += parsed
            totals[key]["has_numeric"] = True
        else:
            totals[key]["non_numeric"].append(row["quantity"])

    items = []
    for (name, unit), data in sorted(totals.items()):
        if data["has_numeric"]:
            items.append({"name": name, "quantity": _format_quantity(data["numeric"]), "unit": unit})
        for qty in sorted(set(data["non_numeric"])):
            items.append({"name": name, "quantity": qty, "unit": unit})

    return render_template("shopping_list.html", items=items)


@main.route("/pantry")
def pantry():
    db = get_db()
    pantry_items = db.execute("SELECT * FROM pantry_items ORDER BY name").fetchall()
    pantry_names = [item["name"].lower() for item in pantry_items]

    recipes = []
    almost_recipes = []
    if pantry_names:
        placeholders = ",".join("?" * len(pantry_names))
        recipes = db.execute(
            f"SELECT r.* FROM recipes r "
            f"JOIN recipe_ingredients ri ON r.id = ri.recipe_id "
            f"JOIN ingredients i ON i.id = ri.ingredient_id "
            f"GROUP BY r.id "
            f"HAVING COUNT(*) = SUM(CASE WHEN LOWER(i.name) IN ({placeholders}) THEN 1 ELSE 0 END) "
            f"ORDER BY r.name",
            pantry_names
        ).fetchall()

        almost_rows = db.execute(
            f"SELECT r.*, COUNT(*) - SUM(CASE WHEN LOWER(i.name) IN ({placeholders}) THEN 1 ELSE 0 END) AS missing_count "
            f"FROM recipes r "
            f"JOIN recipe_ingredients ri ON r.id = ri.recipe_id "
            f"JOIN ingredients i ON i.id = ri.ingredient_id "
            f"GROUP BY r.id "
            f"HAVING missing_count BETWEEN 1 AND 2 "
            f"ORDER BY missing_count, r.name",
            pantry_names
        ).fetchall()

        for row in almost_rows:
            missing = db.execute(
                f"SELECT i.name FROM recipe_ingredients ri "
                f"JOIN ingredients i ON i.id = ri.ingredient_id "
                f"WHERE ri.recipe_id = ? AND LOWER(i.name) NOT IN ({placeholders}) "
                f"ORDER BY i.name",
                [row["id"]] + pantry_names
            ).fetchall()
            almost_recipes.append({
                "recipe": row,
                "missing": [m["name"] for m in missing],
            })

    all_ingredients = db.execute("SELECT name FROM ingredients ORDER BY name").fetchall()
    return render_template(
        "pantry.html",
        recipes=recipes,
        almost_recipes=almost_recipes,
        pantry_items=pantry_items,
        all_ingredients=all_ingredients,
    )


@main.route("/pantry/add", methods=["POST"])
def pantry_add():
    db = get_db()
    name = request.form.get("name", "").strip()
    if name:
        existing = db.execute("SELECT id FROM pantry_items WHERE LOWER(name) = LOWER(?)", (name,)).fetchone()
        if not existing:
            db.execute("INSERT INTO pantry_items (name) VALUES (?)", (name,))
            db.commit()
    return redirect(url_for("main.pantry"))


@main.route("/pantry/remove/<int:item_id>", methods=["POST"])
def pantry_remove(item_id):
    db = get_db()
    db.execute("DELETE FROM pantry_items WHERE id = ?", (item_id,))
    db.commit()
    return redirect(url_for("main.pantry"))


@main.route("/search")
def search():
    db = get_db()
    selected = request.args.getlist("ingredients")
    selected_tags = request.args.getlist("tags")
    query = request.args.get("q", "").strip()

    recipes = []
    if selected or selected_tags or query:
        if selected:
            placeholders = ",".join("?" * len(selected))
            recipes = db.execute(
                f"SELECT DISTINCT r.* FROM recipes r "
                f"JOIN recipe_ingredients ri ON r.id = ri.recipe_id "
                f"JOIN ingredients i ON i.id = ri.ingredient_id "
                f"WHERE i.name IN ({placeholders})",
                selected
            ).fetchall()
        else:
            recipes = db.execute("SELECT * FROM recipes").fetchall()

        if selected_tags:
            def matches_tags(recipe):
                recipe_tags = {t.strip().lower() for t in (recipe["tags"] or "").split(",") if t.strip()}
                return all(t.lower() in recipe_tags for t in selected_tags)
            recipes = [r for r in recipes if matches_tags(r)]

        if query:
            q_lower = query.lower()
            recipes = [
                r for r in recipes
                if q_lower in (r["name"] or "").lower() or q_lower in (r["instructions"] or "").lower()
            ]

    all_tags_rows = db.execute("SELECT tags FROM recipes WHERE tags IS NOT NULL AND tags != ''").fetchall()
    all_tags = sorted({tag.strip() for row in all_tags_rows for tag in row["tags"].split(",") if tag.strip()})

    all_ingredients = db.execute("SELECT name FROM ingredients ORDER BY name").fetchall()
    return render_template(
        "search.html",
        recipes=recipes,
        all_ingredients=all_ingredients,
        selected=selected,
        all_tags=all_tags,
        selected_tags=selected_tags,
        query=query,
    )
