# Database

SQLite database stored as `cookbook.db` in the project root. Schema is defined in `database/schema.sql`.

## Tables

### recipes
Stores each recipe as a single row.

| Column       | Type    | Description                          |
|--------------|---------|--------------------------------------|
| id           | INTEGER | Primary key                          |
| name         | TEXT    | Recipe name                          |
| instructions | TEXT    | Step-by-step cooking instructions    |
| prep_time    | INTEGER | Prep time in minutes                 |
| cook_time    | INTEGER | Cook time in minutes                 |
| servings     | INTEGER | Number of servings                   |
| tags         | TEXT    | Comma-separated tags (e.g. vegan)    |

### ingredients
Stores individual ingredients. Each ingredient is stored once and shared across recipes.

| Column      | Type | Description                                  |
|-------------|------|----------------------------------------------|
| id          | INTEGER | Primary key                               |
| name        | TEXT    | Ingredient name (unique)                  |
| substitutes | TEXT    | Comma-separated substitute ingredient names|

### recipe_ingredients
Join table linking recipes to their ingredients, with quantity info.

| Column        | Type    | Description                    |
|---------------|---------|--------------------------------|
| recipe_id     | INTEGER | Foreign key → recipes.id       |
| ingredient_id | INTEGER | Foreign key → ingredients.id   |
| quantity      | TEXT    | Amount (e.g. "2")              |
| unit          | TEXT    | Unit (e.g. "cups", "tbsp")     |

## Relationships

A recipe has many ingredients through `recipe_ingredients`. An ingredient can belong to many recipes (many-to-many). Substitutions are stored as a text field on the ingredient row.
