# My agent: Smart Pantry & Health-Focused Personal Chef Concierge

One-liner: A conversational agent that helps users manage pantry ingredients, compute meal nutrition, and plan meals tailored for health goals including controlling cholesterol & blood sugar, boosting cognitive/memory power, and optimizing BMI.

## Tool Coverage:

- **Memory**: Remembers health & dietary goals (low cholesterol, low glycemic index / blood sugar control, memory/brain-boosting nutrients, BMI targets), food allergies, household size, and past meal feedback across sessions.
- **Tools**: 
  - `search_recipes(query, health_targets)`: Looks up recipes matching health goals (e.g. low-glycemic, low-cholesterol, omega-3/antioxidant rich).
  - `get_pantry_inventory()`: Checks current pantry items and quantities.
  - `add_to_shopping_list(ingredients)`: Adds missing healthy ingredients to a persistent list.
  - `calculate_health_metrics(recipe, user_profile)`: Calculates impact on cholesterol index, glycemic load, cognitive nutrients, and calorie/macro goals for BMI.
- **Catalog/UI**: Recipe cards (prep time, glycemic rating, cholesterol impact, brain-food tags) and Pantry Inventory tables using A2UI.
- **Image Gen**: Generates appetizing dish presentation visuals and healthy plating suggestions for recipes.
- **Sandbox**: Computes nutritional macros, glycemic index scores, calorie-to-BMI targets, and scales ingredient proportions for serving sizes.

## Recommended Features:
- Vertex AI Memory Bank for long-term health metrics & user preferences
- Firestore for recipe catalog & persistent pantry inventory
- A2UI interactive cards for health-focused recipe recommendations
- Image Generation tool (`gemini-3.1-flash-lite-image`) for dish presentation photos

## Stretch / Extension Ideas:
- Integration with external Grocery Delivery API / Maps for nearby ingredient shopping.
- Code Sandbox execution for personalized BMI & metabolic calculation models.
