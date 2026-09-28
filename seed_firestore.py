import os
from google.cloud import firestore

# CRITICAL: Hardcode the Project ID string explicitly.
# Never use google.auth.default() or GOOGLE_CLOUD_PROJECT for Firestore Client,
# as Agent Platform sets GOOGLE_CLOUD_PROJECT to the project NUMBER, breaking Firestore.
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-02-07cb7cdcf8d2"

db = firestore.Client(project=FIRESTORE_PROJECT_ID)

INITIAL_RECIPES = [
    {
        "id": "recipe_001",
        "name": "Wild Salmon with Quinoa & Roasted Walnuts",
        "description": "Rich in Omega-3 fatty acids and low-glycemic complex carbs for brain health & heart protection.",
        "glycemic_index": "Low",
        "cholesterol_impact": "Lowers LDL",
        "brain_boosting_nutrients": ["Omega-3 DHA", "DHA", "Vitamin E", "Antioxidants"],
        "calories_per_serving": 480,
        "protein_g": 38.0,
        "carbs_g": 32.0,
        "fat_g": 20.0,
        "ingredients": ["Salmon Fillet", "Quinoa", "Walnuts", "Olive Oil", "Spinach", "Lemon"],
        "instructions": "Pan-sear salmon in olive oil. Serve over cooked quinoa with toasted walnuts and fresh spinach."
    },
    {
        "id": "recipe_002",
        "name": "Blueberry Spinach Brain-Boost Smoothie",
        "description": "Antioxidant-packed smoothie designed for cognitive sharpness and stable blood sugar.",
        "glycemic_index": "Low",
        "cholesterol_impact": "Low Saturated Fat",
        "brain_boosting_nutrients": ["Flavonoids", "Anthocyanins", "Folate"],
        "calories_per_serving": 240,
        "protein_g": 12.0,
        "carbs_g": 35.0,
        "fat_g": 6.0,
        "ingredients": ["Wild Blueberries", "Baby Spinach", "Almond Milk", "Chia Seeds", "Plant Protein Powder"],
        "instructions": "Blend all ingredients until smooth. Top with extra chia seeds."
    },
    {
        "id": "recipe_003",
        "name": "Avocado & Chickpea Power Salad",
        "description": "High fiber and monounsaturated fats that stabilize blood glucose and support healthy cholesterol.",
        "glycemic_index": "Low",
        "cholesterol_impact": "Lowers LDL",
        "brain_boosting_nutrients": ["Vitamin E", "Folate", "Polyphenols"],
        "calories_per_serving": 390,
        "protein_g": 14.0,
        "carbs_g": 42.0,
        "fat_g": 18.0,
        "ingredients": ["Chickpeas", "Avocado", "Cherry Tomatoes", "Cucumber", "Extra Virgin Olive Oil", "Lemon Juice"],
        "instructions": "Toss rinsed chickpeas, diced avocado, tomatoes, and cucumber with olive oil and lemon juice."
    },
    {
        "id": "recipe_004",
        "name": "Turmeric Golden Lentil & Kale Soup",
        "description": "Anti-inflammatory turmeric and kale combined with nutrient-dense lentils for steady energy.",
        "glycemic_index": "Low",
        "cholesterol_impact": "Lowers LDL",
        "brain_boosting_nutrients": ["Curcumin", "Iron", "Vitamin K"],
        "calories_per_serving": 310,
        "protein_g": 18.0,
        "carbs_g": 48.0,
        "fat_g": 5.0,
        "ingredients": ["Brown Lentils", "Kale", "Ground Turmeric", "Garlic", "Vegetable Broth", "Olive Oil"],
        "instructions": "Simmer lentils with garlic and turmeric. Stir in chopped kale during the last 5 minutes."
    }
]

INITIAL_PANTRY_ITEMS = [
    {"id": "pantry_001", "name": "Salmon Fillet", "quantity": 4, "unit": "pieces", "category": "Proteins"},
    {"id": "pantry_002", "name": "Wild Blueberries", "quantity": 500, "unit": "grams", "category": "Fruits"},
    {"id": "pantry_003", "name": "Extra Virgin Olive Oil", "quantity": 750, "unit": "ml", "category": "Oils & Fats"},
    {"id": "pantry_004", "name": "Walnuts", "quantity": 300, "unit": "grams", "category": "Nuts & Seeds"},
    {"id": "pantry_005", "name": "Chickpeas", "quantity": 3, "unit": "cans", "category": "Legumes"}
]

def seed_database():
    print(f"Seeding Firestore in project '{FIRESTORE_PROJECT_ID}'...")
    
    # Seed Recipes
    recipes_ref = db.collection("recipes")
    for r in INITIAL_RECIPES:
        doc_id = r["id"]
        recipes_ref.document(doc_id).set(r)
        print(f"  ✓ Seeded Recipe: {r['name']}")

    # Seed Pantry Items
    pantry_ref = db.collection("pantry_items")
    for p in INITIAL_PANTRY_ITEMS:
        doc_id = p["id"]
        pantry_ref.document(doc_id).set(p)
        print(f"  ✓ Seeded Pantry Item: {p['name']}")

    print("\n✅ Firestore seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
