# Routes

All routes are defined in `app/routes.py` and registered under the `main` Blueprint.

## Pages

| Route                | Method | Description                                      |
|----------------------|--------|--------------------------------------------------|
| `/`                  | GET    | Lists all recipes                                |
| `/recipe/<id>`       | GET    | Shows a single recipe with ingredients and steps |
| `/search`            | GET    | Search recipes by selecting available ingredients|

## Search Logic

The `/search` route accepts a list of ingredient names as query parameters (`?ingredients=egg&ingredients=flour`). It returns any recipe that contains at least one of the selected ingredients. Results are rendered on the same page as the ingredient checkboxes.
