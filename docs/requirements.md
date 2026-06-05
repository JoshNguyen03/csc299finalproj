# Requirements

## Functional Requirements

### Core
- Users can view a list of all recipes
- Users can view a single recipe with its ingredients, quantities, and instructions
- Users can search for recipes by selecting ingredients they have on hand
- The app recommends ingredient substitutions where available

### Potential Features
- Filter recipes by dietary tags (vegetarian, vegan, gluten-free, etc.)
- Scale ingredient quantities based on desired serving size
- Plan meals for the week and generate a combined shopping list
- Display nutritional information aggregated from ingredients
- Rate or favorite recipes

## Non-Functional Requirements

- The app runs locally in a web browser
- All data is persisted in a SQLite database
- Pages are served server-side — no frontend JavaScript framework required
- The app is written in Python using Flask

## Out of Scope

- User accounts or authentication
- Deployment to a public server
- Mobile-specific design
