"""
Indian Recipe Dataset Generator - 100,000+ Records
Generates realistic Indian recipe data with efficient batch writing
Focus: 80% Vegetarian Indian Cuisine
"""

import csv
import json
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict
import os

# ==========================================
# CONFIGURATION
# ==========================================

TOTAL_RECORDS = 100000
BATCH_SIZE = 5000  # Write in batches to save memory
CSV_FILE = 'recipes.csv'
JSON_FILE = 'recipes.json'

# ==========================================
# DATA POOLS - Indian Recipe Elements
# ==========================================

CUISINES = {
    'North Indian': 0.25,
    'South Indian': 0.20,
    'Punjabi': 0.15,
    'Bengali': 0.10,
    'Gujarati': 0.10,
    'Maharashtrian': 0.08,
    'Rajasthani': 0.05,
    'Hyderabadi': 0.04,
    'Goan': 0.03
}

DIFFICULTIES = {
    'Beginner': 0.40,
    'Intermediate': 0.45,
    'Advanced': 0.15
}

# Indian ingredients with calorie data (per 100g)
INGREDIENTS = {
    # Proteins
    'paneer': 265, 'chicken': 165, 'mutton': 294, 'fish': 96,
    'eggs': 155, 'prawns': 99, 'dal': 116, 'chickpeas': 164,
    'kidney beans': 127, 'black lentils': 116, 'green moong dal': 105,
    'toor dal': 335, 'chana dal': 357, 'masoor dal': 116,
    
    # Dairy
    'milk': 42, 'yogurt': 59, 'ghee': 900, 'butter': 717,
    'cream': 340, 'khoya': 400, 'curd': 60, 'buttermilk': 40,
    
    # Grains & Carbs
    'rice': 130, 'basmati rice': 130, 'wheat flour': 340, 'roti': 260,
    'naan': 260, 'paratha': 290, 'puri': 325, 'dosa': 112,
    'idli': 65, 'upma': 85, 'poha': 130, 'semolina': 360,
    
    # Vegetables
    'potatoes': 77, 'tomatoes': 18, 'onions': 40, 'garlic': 149,
    'ginger': 80, 'green chillies': 40, 'cauliflower': 25,
    'peas': 81, 'carrots': 41, 'beans': 31, 'cabbage': 25,
    'spinach': 23, 'fenugreek leaves': 49, 'bottle gourd': 14,
    'bitter gourd': 17, 'brinjal': 25, 'okra': 33, 'capsicum': 31,
    'drumsticks': 26, 'ridge gourd': 20, 'pumpkin': 26,
    
    # Spices & Masalas
    'turmeric': 0, 'red chilli powder': 0, 'coriander powder': 0,
    'cumin seeds': 0, 'mustard seeds': 0, 'fenugreek seeds': 0,
    'garam masala': 0, 'curry leaves': 0, 'bay leaves': 0,
    'cardamom': 0, 'cinnamon': 0, 'cloves': 0, 'black pepper': 0,
    'asafoetida': 0, 'carom seeds': 0, 'fennel seeds': 0,
    'coriander leaves': 23, 'mint leaves': 44, 'kasuri methi': 0,
    
    # Oils & Fats
    'mustard oil': 884, 'coconut oil': 862, 'sunflower oil': 884,
    'sesame oil': 884, 'groundnut oil': 884,
    
    # Legumes & Pulses
    'rajma': 127, 'kabuli chana': 164, 'black chana': 164,
    'green gram': 105, 'horse gram': 321,
    
    # Nuts & Seeds
    'cashews': 553, 'almonds': 579, 'peanuts': 567,
    'sesame seeds': 573, 'poppy seeds': 525, 'coconut': 354,
    
    # Condiments & Others
    'tamarind': 239, 'jaggery': 383, 'sugar': 387, 'salt': 0,
    'lemon juice': 22, 'coconut milk': 230, 'tomato puree': 38,
    'ginger-garlic paste': 100, 'green chutney': 50, 'pickle': 60,
    
    # Specialty Items
    'besan': 387, 'cornflour': 381, 'rice flour': 366,
    'vermicelli': 348, 'sago': 358, 'dry fruits': 500
}

VEGETARIAN_INGREDIENTS = [
    'paneer', 'dal', 'chickpeas', 'kidney beans', 'black lentils',
    'green moong dal', 'toor dal', 'chana dal', 'masoor dal',
    'milk', 'yogurt', 'ghee', 'curd', 'khoya',
    'rice', 'basmati rice', 'wheat flour', 'roti', 'besan',
    'potatoes', 'tomatoes', 'onions', 'cauliflower', 'peas',
    'spinach', 'fenugreek leaves', 'brinjal', 'okra', 'capsicum',
    'cashews', 'almonds', 'coconut', 'tamarind', 'jaggery'
]

NON_VEG_INGREDIENTS = [
    'chicken', 'mutton', 'fish', 'prawns', 'eggs'
]

COOKING_VERBS = [
    'Heat', 'Chop', 'Dice', 'Slice', 'Mix', 'Stir', 'Sauté', 'Boil',
    'Simmer', 'Cook', 'Roast', 'Fry', 'Deep fry', 'Shallow fry',
    'Grind', 'Blend', 'Temper', 'Season', 'Add', 'Pour', 'Strain',
    'Garnish', 'Marinate', 'Knead', 'Roll', 'Steam', 'Pressure cook'
]

# Popular Indian dish templates
VEG_DISHES = [
    'Paneer Butter Masala', 'Dal Makhani', 'Chole Masala', 'Palak Paneer',
    'Aloo Gobi', 'Baingan Bharta', 'Bhindi Masala', 'Malai Kofta',
    'Vegetable Biryani', 'Veg Pulao', 'Jeera Rice', 'Lemon Rice',
    'Sambar', 'Rasam', 'Dosa', 'Idli', 'Vada', 'Uttapam',
    'Poha', 'Upma', 'Pav Bhaji', 'Misal Pav', 'Vada Pav',
    'Dhokla', 'Khandvi', 'Thepla', 'Paratha', 'Aloo Paratha',
    'Rajma Masala', 'Kadhi Pakora', 'Dal Tadka', 'Chana Masala',
    'Mixed Veg Curry', 'Paneer Tikka', 'Veg Korma', 'Navratan Korma'
]

NON_VEG_DISHES = [
    'Butter Chicken', 'Chicken Tikka Masala', 'Tandoori Chicken',
    'Chicken Biryani', 'Mutton Rogan Josh', 'Keema Curry',
    'Fish Curry', 'Prawn Curry', 'Egg Curry', 'Chicken Korma',
    'Mutton Biryani', 'Chicken Kadai', 'Fish Fry', 'Chicken 65',
    'Mutton Curry', 'Chicken Chettinad', 'Goan Fish Curry',
    'Hyderabadi Mutton', 'Bengali Fish Curry', 'Egg Biryani'
]

TAGS_POOL = [
    'spicy', 'mild', 'tangy', 'sweet', 'savory', 'healthy', 'comfort food',
    'quick meal', 'meal prep', 'protein-rich', 'low-calorie', 'high-fiber',
    'gluten-free', 'vegan', 'vegetarian', 'non-vegetarian', 'breakfast',
    'lunch', 'dinner', 'snack', 'appetizer', 'main course', 'side dish',
    'curry', 'dal', 'rice dish', 'bread', 'street food', 'festive',
    'traditional', 'authentic', 'home-style', 'restaurant-style',
    'one-pot', 'pressure cooker', 'grilled', 'fried', 'steamed', 'baked'
]

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def weighted_choice(choices: Dict) -> str:
    """Select item based on weighted probabilities"""
    items = list(choices.keys())
    weights = list(choices.values())
    return random.choices(items, weights=weights, k=1)[0]


def generate_recipe_title(cuisine: str, is_veg: bool) -> str:
    """Generate realistic Indian recipe title"""
    
    adjectives = ['Authentic', 'Traditional', 'Homestyle', 'Restaurant Style',
                  'Classic', 'Delicious', 'Easy', 'Quick', 'Spicy', 'Creamy',
                  'Dhaba Style', 'Punjabi', 'Mumbai Style', 'South Indian',
                  'North Indian', 'Bengali Style', 'Hyderabadi']
    
    dishes = VEG_DISHES if is_veg else NON_VEG_DISHES
    
    use_adjective = random.random() < 0.6
    
    if use_adjective:
        return f"{random.choice(adjectives)} {random.choice(dishes)}"
    else:
        return f"{cuisine} {random.choice(dishes)}"


def select_ingredients(is_veg: bool, count: int) -> List[str]:
    """Select random ingredients based on vegetarian preference"""
    
    if is_veg:
        available = VEGETARIAN_INGREDIENTS.copy()
    else:
        available = VEGETARIAN_INGREDIENTS.copy()
        available.extend(NON_VEG_INGREDIENTS)
    
    # Add more random ingredients from main pool
    all_ingredients = list(INGREDIENTS.keys())
    available.extend(random.sample(all_ingredients, min(30, len(all_ingredients))))
    
    # Remove duplicates
    available = list(set(available))
    
    # Select ingredients
    selected = random.sample(available, min(count, len(available)))
    
    return selected


def generate_ingredient_quantities(ingredients: List[str]) -> Dict[str, float]:
    """Generate realistic quantities in grams for each ingredient"""
    
    quantities = {}
    
    for ingredient in ingredients:
        # Spices and masalas: 1-10 grams
        if ingredient in ['turmeric', 'red chilli powder', 'coriander powder',
                          'garam masala', 'cumin seeds', 'mustard seeds', 'asafoetida']:
            quantities[ingredient] = round(random.uniform(1, 10), 1)
        
        # Oils and ghee: 15-40 grams
        elif ingredient in ['ghee', 'mustard oil', 'coconut oil', 'sunflower oil']:
            quantities[ingredient] = round(random.uniform(15, 40), 1)
        
        # Proteins (paneer, chicken, mutton): 250-500 grams
        elif ingredient in ['paneer', 'chicken', 'mutton', 'fish', 'prawns']:
            quantities[ingredient] = round(random.uniform(250, 500), 1)
        
        # Dals and lentils: 150-300 grams
        elif 'dal' in ingredient or ingredient in ['chickpeas', 'kidney beans', 'rajma']:
            quantities[ingredient] = round(random.uniform(150, 300), 1)
        
        # Rice and grains: 200-400 grams
        elif ingredient in ['rice', 'basmati rice', 'wheat flour']:
            quantities[ingredient] = round(random.uniform(200, 400), 1)
        
        # Main vegetables: 100-250 grams
        elif ingredient in ['potatoes', 'tomatoes', 'onions', 'cauliflower', 'spinach']:
            quantities[ingredient] = round(random.uniform(100, 250), 1)
        
        # Fresh herbs: 10-30 grams
        elif ingredient in ['coriander leaves', 'mint leaves', 'curry leaves']:
            quantities[ingredient] = round(random.uniform(10, 30), 1)
        
        # Others: 30-150 grams
        else:
            quantities[ingredient] = round(random.uniform(30, 150), 1)
    
    return quantities


def calculate_total_calories(ingredient_quantities: Dict[str, float]) -> int:
    """Calculate total calories based on ingredients and quantities"""
    
    total_calories = 0
    
    for ingredient, quantity_grams in ingredient_quantities.items():
        if ingredient in INGREDIENTS:
            calories_per_100g = INGREDIENTS[ingredient]
            ingredient_calories = (calories_per_100g * quantity_grams) / 100
            total_calories += ingredient_calories
    
    return int(total_calories)


def generate_cooking_steps(num_steps: int, ingredients: List[str], is_veg: bool) -> List[str]:
    """Generate realistic Indian cooking steps"""
    
    steps = []
    
    # Indian cooking specific templates
    templates = [
        f"Heat {random.choice(['ghee', 'oil'])} in a {random.choice(['kadhai', 'pan', 'pressure cooker'])}.",
        f"Add cumin seeds and let them splutter.",
        f"Add finely chopped onions and sauté until golden brown.",
        f"Add ginger-garlic paste and cook for 1-2 minutes.",
        f"Add chopped tomatoes and cook until they turn mushy.",
        f"Add turmeric, red chilli powder, and coriander powder. Mix well.",
        f"Add {random.choice(ingredients)} and cook for {random.randint(5, 15)} minutes.",
        f"Add salt to taste and mix thoroughly.",
        f"Simmer on low heat for {random.randint(10, 20)} minutes.",
        f"Garnish with fresh coriander leaves and serve hot.",
        f"Add garam masala and give it a final stir.",
        f"Serve hot with {random.choice(['roti', 'naan', 'rice', 'paratha'])}."
    ]
    
    for i in range(num_steps):
        if i == 0:
            steps.append("Wash and prepare all ingredients. Chop vegetables as needed.")
        elif i == num_steps - 1:
            steps.append("Garnish with fresh coriander leaves and serve hot with roti or rice.")
        else:
            steps.append(random.choice(templates))
    
    return steps


def estimate_cooking_time(difficulty: str, num_steps: int) -> int:
    """Estimate cooking time based on difficulty and steps"""
    
    base_time = {
        'Beginner': random.randint(20, 35),
        'Intermediate': random.randint(35, 60),
        'Advanced': random.randint(60, 90)
    }
    
    time = base_time[difficulty] + (num_steps * random.randint(3, 6))
    
    return min(time, 150)  # Cap at 2.5 hours


def generate_tags(is_veg: bool, cuisine: str, difficulty: str) -> List[str]:
    """Generate relevant tags for the recipe"""
    
    tags = []
    
    # Add vegetarian/non-vegetarian tag
    if is_veg:
        tags.append('vegetarian')
    else:
        tags.append('non-vegetarian')
    
    # Add cuisine-specific tags
    tags.append('indian')
    
    # Add difficulty-based tags
    if difficulty == 'Beginner':
        tags.extend(['easy', 'quick meal'])
    elif difficulty == 'Advanced':
        tags.append('traditional')
    
    # Add random tags
    num_tags = random.randint(2, 4)
    available_tags = [t for t in TAGS_POOL if t not in tags]
    tags.extend(random.sample(available_tags, min(num_tags, len(available_tags))))
    
    return tags[:7]  # Limit to 7 tags


def random_date(start_year: int = 2020) -> str:
    """Generate random timestamp"""
    start = datetime(start_year, 1, 1)
    end = datetime.now()
    
    delta = end - start
    random_days = random.randint(0, delta.days)
    random_seconds = random.randint(0, 86400)
    
    random_date = start + timedelta(days=random_days, seconds=random_seconds)
    
    return random_date.isoformat()


def generate_recipe() -> Dict:
    """Generate a single Indian recipe record"""
    
    # 80% vegetarian, 20% non-vegetarian
    is_veg = random.random() < 0.80
    
    # Select cuisine and difficulty
    cuisine = weighted_choice(CUISINES)
    difficulty = weighted_choice(DIFFICULTIES)
    
    # Generate title
    title = generate_recipe_title(cuisine, is_veg)
    
    # Select ingredients (6-18 items for Indian recipes)
    num_ingredients = random.randint(6, 18)
    ingredients = select_ingredients(is_veg, num_ingredients)
    
    # Generate quantities
    ingredient_quantities = generate_ingredient_quantities(ingredients)
    
    # Calculate calories
    calories = calculate_total_calories(ingredient_quantities)
    
    # Generate cooking steps (4-12 steps)
    num_steps = random.randint(4, 12)
    steps = generate_cooking_steps(num_steps, ingredients, is_veg)
    
    # Estimate time
    estimated_time = estimate_cooking_time(difficulty, num_steps)
    
    # Generate tags
    tags = generate_tags(is_veg, cuisine, difficulty)
    
    # Generate rating (skewed towards higher ratings)
    rating = round(random.triangular(3.5, 5.0, 4.5), 1)
    
    # Create recipe record
    recipe = {
        'recipe_id': str(uuid.uuid4()),
        'title': title,
        'ingredients': ingredients,
        'ingredient_quantities': ingredient_quantities,
        'calories': calories,
        'steps': steps,
        'estimated_time': estimated_time,
        'difficulty': difficulty,
        'cuisine': cuisine,
        'is_veg': is_veg,
        'tags': tags,
        'rating': rating,
        'created_at': random_date()
    }
    
    return recipe


# ==========================================
# MAIN GENERATION & WRITING FUNCTIONS
# ==========================================

def write_csv_batch(filename: str, recipes: List[Dict], mode: str = 'a'):
    """Write batch of recipes to CSV file"""
    
    fieldnames = [
        'recipe_id', 'title', 'ingredients', 'ingredient_quantities',
        'calories', 'steps', 'estimated_time', 'difficulty',
        'cuisine', 'is_veg', 'tags', 'rating', 'created_at'
    ]
    
    with open(filename, mode, newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if mode == 'w':
            writer.writeheader()
        
        for recipe in recipes:
            recipe_copy = recipe.copy()
            recipe_copy['ingredients'] = '|'.join(recipe['ingredients'])
            recipe_copy['ingredient_quantities'] = json.dumps(recipe['ingredient_quantities'])
            recipe_copy['steps'] = '|'.join(recipe['steps'])
            recipe_copy['tags'] = '|'.join(recipe['tags'])
            
            writer.writerow(recipe_copy)


def write_json_batch(filename: str, recipes: List[Dict], mode: str = 'a'):
    """Write batch of recipes to JSON file (JSON Lines format)"""
    
    with open(filename, mode, encoding='utf-8') as f:
        for recipe in recipes:
            f.write(json.dumps(recipe) + '\n')


def generate_dataset():
    """Main function to generate complete dataset"""
    
    print("=" * 60)
    print("🍛 Indian Recipe Dataset Generator - 100k+ Records")
    print("=" * 60)
    print(f"📊 Total Records: {TOTAL_RECORDS:,}")
    print(f"📦 Batch Size: {BATCH_SIZE:,}")
    print(f"🥗 Vegetarian: ~80% | Non-Veg: ~20%")
    print(f"💾 Output Files: {CSV_FILE}, {JSON_FILE}")
    print("=" * 60)
    
    # Initialize files
    open(CSV_FILE, 'w').close()
    open(JSON_FILE, 'w').close()
    
    batches = (TOTAL_RECORDS + BATCH_SIZE - 1) // BATCH_SIZE
    
    for batch_num in range(batches):
        batch_start = batch_num * BATCH_SIZE
        batch_end = min(batch_start + BATCH_SIZE, TOTAL_RECORDS)
        current_batch_size = batch_end - batch_start
        
        print(f"\n⏳ Generating batch {batch_num + 1}/{batches} ({batch_start + 1:,} to {batch_end:,})...")
        
        # Generate batch of recipes
        recipes_batch = []
        for i in range(current_batch_size):
            recipes_batch.append(generate_recipe())
        
        # Write to files
        mode = 'w' if batch_num == 0 else 'a'
        write_csv_batch(CSV_FILE, recipes_batch, mode=mode)
        write_json_batch(JSON_FILE, recipes_batch, mode=mode)
        
        print(f"✅ Batch {batch_num + 1} written ({current_batch_size:,} records)")
    
    print("\n" + "=" * 60)
    print(f"✅ Dataset generation complete!")
    print(f"📄 CSV File: {CSV_FILE} ({os.path.getsize(CSV_FILE) / (1024**2):.2f} MB)")
    print(f"📄 JSON File: {JSON_FILE} ({os.path.getsize(JSON_FILE) / (1024**2):.2f} MB)")
    print("=" * 60)
    
    # Generate sample preview
    print("\n📋 Sample Preview (First 3 Records):\n")
    
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= 3:
                break
            print(f"Record {i+1}:")
            print(f"  Title: {row['title']}")
            print(f"  Cuisine: {row['cuisine']}")
            print(f"  Difficulty: {row['difficulty']}")
            print(f"  Calories: {row['calories']}")
            print(f"  Time: {row['estimated_time']} minutes")
            print(f"  Vegetarian: {row['is_veg']}")
            print(f"  Rating: {row['rating']}")
            print()


if __name__ == '__main__':
    generate_dataset()