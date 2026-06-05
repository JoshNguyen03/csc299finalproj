# Project Overview

Interactive cookbook web app built with Flask and SQLite. Users can browse recipes, view ingredients and instructions, and search for recipes based on ingredients they have on hand.

## Project Structure

```
csc299finalproj/
├── app.py                  # Entry point — runs the Flask app
├── app/
│   ├── __init__.py         # App factory, database connection helpers
│   ├── routes.py           # URL route handlers
│   ├── templates/          # Jinja2 HTML templates
│   │   ├── base.html       # Shared layout (nav, head)
│   │   ├── index.html      # Recipe list page
│   │   ├── recipe.html     # Single recipe detail page
│   │   └── search.html     # Ingredient search page
│   └── static/
│       └── style.css       # Basic styles
├── database/
│   └── schema.sql          # SQLite table definitions
└── docs/
    ├── overview.md         # This file
    ├── database.md         # Database schema explanation
    └── routes.md           # Route and page descriptions
```

## How It Works

1. The browser makes a request to a Flask route.
2. The route queries the SQLite database using `sqlite3`.
3. Flask renders an HTML page using a Jinja2 template and returns it to the browser.

No JavaScript framework or REST API is used — all logic lives in Python.
