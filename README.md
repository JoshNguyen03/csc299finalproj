# csc299finalproj


[WIP]Prompt/Outline:

For my project I want to make a personal interactive cookbook. It will use recipes as nodes and things like ingredients, time, etc. as relations similar to the concept graph. I want to be able to search up recipes depending on the selected ingredients allowing me to figure out what I can make with what I have. The cookbook should recommend subsitutions for ingredients. The project will be a web application built with Flask (Python). Recipe and ingredient data will be stored in a SQLite database, queried through Python's built-in sqlite3 module.


Potential features:
- Dietary filters/tags (vegetarian, vegan, gluten-free, etc.)
- Recipe scaling for different serving sizes
- Meal planning with an auto-generated shopping list
- Nutritional info aggregated from ingredients
- Recipe ratings/favorites

## Getting Started

**Prerequisites:** [UV](https://docs.astral.sh/uv/getting-started/installation/) and Python 3.11+

1. Install dependencies:
   ```
   uv sync
   ```

2. Initialize the database:
   ```
   uv run python -c "import sqlite3; conn = sqlite3.connect('cookbook.db'); conn.executescript(open('database/schema.sql').read()); conn.commit()"
   ```

3. Run the app:
   ```
   uv run app.py
   ```

4. Open your browser and go to `http://localhost:5000`

## Tech Stack

- **Flask** — Python web framework, handles routes and serves pages
- **SQLite** — file-based database, accessed via Python's built-in `sqlite3` module
- **Jinja2** — HTML templating (included with Flask) for rendering pages server-side
