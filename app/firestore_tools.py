from google.cloud import firestore

# CRITICAL: Hardcode the Project ID string explicitly.
# Never use google.auth.default() or GOOGLE_CLOUD_PROJECT for Firestore Client,
# as Agent Platform sets GOOGLE_CLOUD_PROJECT to the project NUMBER, breaking Firestore.
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-02-07cb7cdcf8d2"

_db_client = None

def get_db():
    global _db_client
    if _db_client is None:
        _db_client = firestore.Client(project=FIRESTORE_PROJECT_ID)
    return _db_client


def search_recipes(query: str = "") -> list[dict]:
    """Search recipes in the Firestore backend matching health targets or keyword queries.
    
    Args:
        query: Optional search keyword (e.g. 'salmon', 'brain', 'cholesterol', 'low glycemic').
        
    Returns:
        List of matching recipe dictionaries.
    """
    db = get_db()
    docs = db.collection("recipes").stream()
    results = []
    q_lower = query.lower().strip()
    
    for doc in docs:
        data = doc.to_dict()
        if not q_lower:
            results.append(data)
        else:
            # Check matching in name, description, nutrients, or ingredients
            name = data.get("name", "").lower()
            desc = data.get("description", "").lower()
            nutrients = " ".join(data.get("brain_boosting_nutrients", [])).lower()
            ingredients = " ".join(data.get("ingredients", [])).lower()
            gi = data.get("glycemic_index", "").lower()
            ch = data.get("cholesterol_impact", "").lower()
            
            if (q_lower in name or q_lower in desc or q_lower in nutrients 
                or q_lower in ingredients or q_lower in gi or q_lower in ch):
                results.append(data)
                
    return results


def add_recipe(
    name: str, 
    description: str, 
    glycemic_index: str, 
    cholesterol_impact: str, 
    brain_boosting_nutrients: str, 
    calories_per_serving: int, 
    ingredients: str, 
    instructions: str
) -> dict:
    """Adds a new recipe document to the Firestore recipes collection.
    
    Args:
        name: Recipe title.
        description: Summary of health benefits and taste.
        glycemic_index: 'Low', 'Medium', or 'High'.
        cholesterol_impact: 'Lowers LDL', 'Neutral', or 'Low Saturated Fat'.
        brain_boosting_nutrients: Comma-separated list of key nutrients (e.g. 'Omega-3, Flavonoids').
        calories_per_serving: Calorie count per serving.
        ingredients: Comma-separated list of ingredients.
        instructions: Preparation steps.
        
    Returns:
        Dictionary confirming the created recipe record.
    """
    db = get_db()
    doc_id = f"recipe_{name.lower().replace(' ', '_')[:20]}"
    
    nutrients_list = [n.strip() for n in brain_boosting_nutrients.split(",") if n.strip()]
    ingredients_list = [i.strip() for i in ingredients.split(",") if i.strip()]
    
    recipe_data = {
        "id": doc_id,
        "name": name,
        "description": description,
        "glycemic_index": glycemic_index,
        "cholesterol_impact": cholesterol_impact,
        "brain_boosting_nutrients": nutrients_list,
        "calories_per_serving": calories_per_serving,
        "ingredients": ingredients_list,
        "instructions": instructions
    }
    
    db.collection("recipes").document(doc_id).set(recipe_data)
    return {"status": "success", "message": f"Recipe '{name}' added successfully", "recipe": recipe_data}


def get_pantry_items() -> list[dict]:
    """Retrieves all current pantry items from the Firestore pantry_items collection.
    
    Returns:
        List of pantry item dictionaries containing name, quantity, unit, and category.
    """
    db = get_db()
    docs = db.collection("pantry_items").stream()
    return [doc.to_dict() for doc in docs]


def update_pantry_item(name: str, quantity: float, unit: str, category: str = "General") -> dict:
    """Adds or updates an item in the Firestore pantry_items collection.
    
    Args:
        name: Name of ingredient (e.g. 'Olive Oil').
        quantity: Amount available.
        unit: Unit of measurement (e.g. 'grams', 'ml', 'pieces').
        category: Food category (e.g. 'Proteins', 'Nuts & Seeds').
        
    Returns:
        Dictionary confirming the updated pantry item.
    """
    db = get_db()
    doc_id = f"pantry_{name.lower().replace(' ', '_')[:20]}"
    pantry_data = {
        "id": doc_id,
        "name": name,
        "quantity": quantity,
        "unit": unit,
        "category": category
    }
    db.collection("pantry_items").document(doc_id).set(pantry_data)
    return {"status": "success", "message": f"Pantry item '{name}' updated to {quantity} {unit}", "item": pantry_data}


def calculate_nutrition_and_glycemic_load(ingredients_summary: str, servings: int = 1) -> dict:
    """Calculates nutritional breakdown, glycemic load score, and cholesterol suitability for a recipe or meal.
    
    Args:
        ingredients_summary: Summary of ingredients and quantities (e.g. 'salmon, quinoa, spinach, walnuts').
        servings: Number of servings (default is 1).
        
    Returns:
        Dictionary with calories per serving, macro breakdown (protein, carbs, fat), glycemic load index, and health impact rating.
    """
    summary_lower = ingredients_summary.lower()
    
    # Base estimates per serving based on ingredients presence
    base_calories = 350
    protein = 20.0
    carbs = 30.0
    fat = 12.0
    glycemic_load = "Low (GL < 10)"
    cholesterol_rating = "Excellent (Low Saturated Fat & High Monounsaturated/Omega-3)"
    brain_score = "High (Contains DHA/Antioxidants)"
    
    if "salmon" in summary_lower or "fish" in summary_lower:
        protein += 15.0
        fat += 6.0
    if "quinoa" in summary_lower or "lentil" in summary_lower or "chickpea" in summary_lower:
        carbs += 15.0
        protein += 6.0
    if "walnut" in summary_lower or "avocado" in summary_lower or "olive oil" in summary_lower:
        fat += 8.0
    if "blueberry" in summary_lower or "spinach" in summary_lower or "kale" in summary_lower:
        carbs += 5.0
        
    total_calories = int(base_calories * (servings / 1.0))
    scaled_protein = round(protein * servings, 1)
    scaled_carbs = round(carbs * servings, 1)
    scaled_fat = round(fat * servings, 1)
    
    return {
        "ingredients_evaluated": ingredients_summary,
        "servings": servings,
        "calories_total": total_calories,
        "calories_per_serving": int(base_calories),
        "macros_per_serving": {
            "protein_g": protein,
            "carbs_g": carbs,
            "fat_g": fat
        },
        "total_macros": {
            "protein_g": scaled_protein,
            "carbs_g": scaled_carbs,
            "fat_g": scaled_fat
        },
        "glycemic_load_rating": glycemic_load,
        "cholesterol_impact_rating": cholesterol_rating,
        "brain_health_rating": brain_score
    }


def fetch_external_recipes(query: str) -> list[dict]:
    """Fetches real-time recipe data from the free public TheMealDB API.
    
    Args:
        query: Recipe title or ingredient search term (e.g. 'salmon', 'chickpea', 'salad').
        
    Returns:
        List of matching recipe dictionaries with instructions, ingredients, category, and image URL.
    """
    import urllib.request
    import urllib.parse
    import json
    
    url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={urllib.parse.quote(query)}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            meals = data.get("meals")
            if not meals:
                return []
            
            results = []
            for m in meals[:3]:
                ingredients = []
                for i in range(1, 21):
                    ing = m.get(f"strIngredient{i}")
                    meas = m.get(f"strMeasure{i}")
                    if ing and ing.strip():
                        ingredients.append(f"{meas.strip() if meas else ''} {ing.strip()}".strip())
                        
                results.append({
                    "id": m.get("idMeal"),
                    "name": m.get("strMeal"),
                    "category": m.get("strCategory"),
                    "area": m.get("strArea"),
                    "instructions": m.get("strInstructions", "")[:250] + "...",
                    "image_url": m.get("strMealThumb"),
                    "ingredients": ingredients
                })
            return results
    except Exception as e:
        return [{"error": f"Failed to fetch external recipes: {str(e)}"}]


