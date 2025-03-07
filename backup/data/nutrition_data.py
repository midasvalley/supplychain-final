import requests
import pandas as pd
import time
import os
import uuid
import re
import concurrent.futures
import json
from tqdm import tqdm

# Load your CSV
df = pd.read_csv("fresh_products.csv")

# Clean up product names
df['Product Name'] = df['Product Name'].str.replace('"', '')

# Add a unique identifier to each product
df['UID'] = [str(uuid.uuid4())[:8] for _ in range(len(df))]

# Create a new dataframe for USDA lookup data
usda_df = pd.DataFrame(columns=[
    'UID', 
    'Amazon Name', 
    'USDA Name',
    'USDA Food ID',
    'Match Confidence',
    'Serving Size', 
    'Serving Unit', 
    'Calories', 
    'Protein (g)', 
    'Carbs (g)', 
    'Fat (g)', 
    'Fiber (g)', 
    'Sugar (g)'
])

# USDA API key
api_key = "hrj12UbPsq1NKRF6uePbp5FudbBatEpP3qcbIMNX"
base_url = "https://api.nal.usda.gov/fdc/v1/"

# Function to extract brand name from product name
def extract_brand(product_name):
    # Common brand patterns
    brand_patterns = [
        r'^([\w\s]+?)\s+(?:Brand|by)',  # "Brand by" or just "Brand"
        r'^([\w\s]+?)\s+',              # First word(s) before space
        r'([\w\s]+?)\s+(?:Bar|Protein|Coffee|Pizza|Yogurt|Eggs)'  # Word before product type
    ]
    
    for pattern in brand_patterns:
        match = re.search(pattern, product_name)
        if match:
            brand = match.group(1).strip()
            # Only return if brand is not too generic
            if len(brand) > 2 and brand.lower() not in ['the', 'fresh', 'amazon', 'organic']:
                return brand
    
    return None

# Function to determine product category based on name and units
def determine_product_category(product_name, quantity=None, unit=None):
    product_name_lower = product_name.lower()
    
    # Map of categories and their keywords
    category_keywords = {
        'coffee': ['coffee', 'roast', 'blend', 'espresso', 'caffeine'],
        'meat': ['beef', 'chicken', 'pork', 'turkey', 'sausage', 'bacon', 'steak', 'ground'],
        'seafood': ['shrimp', 'fish', 'salmon', 'tuna', 'crab', 'lobster', 'seafood'],
        'nuts': ['almond', 'peanut', 'cashew', 'pecan', 'walnut', 'pistachio', 'hazelnut', 'nut'],
        'dairy': ['milk', 'cheese', 'yogurt', 'cream', 'butter', 'dairy'],
        'eggs': ['egg', 'eggs'],
        'fruits': ['apple', 'banana', 'orange', 'berry', 'fruit', 'lemon', 'lime', 'blueberry', 'strawberry', 'cranberry'],
        'vegetables': ['vegetable', 'carrot', 'broccoli', 'spinach', 'lettuce', 'tomato', 'potato', 'onion'],
        'snacks': ['bar', 'protein bar', 'snack', 'chip', 'cracker', 'cookie'],
        'beverages': ['drink', 'beverage', 'water', 'juice', 'soda', 'tea'],
        'pizza': ['pizza'],
        'oil': ['oil', 'olive oil'],
        'breakfast': ['cereal', 'oatmeal', 'breakfast']
    }
    
    # Check for category matches in product name
    for category, keywords in category_keywords.items():
        if any(keyword in product_name_lower for keyword in keywords):
            return category
    
    # Use unit information as a fallback
    if unit:
        unit_lower = unit.lower()
        if unit_lower in ['oz', 'ounce'] and quantity and quantity > 10:
            return 'beverages'  # Likely a beverage if sold in larger ounces
        elif unit_lower in ['count', 'each'] and 'bar' in product_name_lower:
            return 'snacks'  # Likely snack bars if sold in count
        elif unit_lower in ['lb', 'pound']:
            return 'meat'  # Likely meat if sold by pound
    
    return 'other'

# Function to clean and prepare search terms
def prepare_search_terms(product_name, quantity=None, unit=None):
    # Extract key product information
    main_terms = []
    
    # Remove common filler words and packaging info
    cleaned = re.sub(r'\(.*?\)', '', product_name)  # Remove parentheses and their contents
    cleaned = re.sub(r'[\d]+ (?:Count|oz|lb|Pack|g)\b', '', cleaned, flags=re.IGNORECASE)  # Remove quantities
    cleaned = re.sub(r'(?:with|by|from|for|and)\b', '', cleaned, flags=re.IGNORECASE)  # Remove common prepositions
    
    # Extract brand if possible
    brand = extract_brand(product_name)
    
    # Get the main product type
    product_type = cleaned.split(',')[0].strip()
    
    # Determine product category
    category = determine_product_category(product_name, quantity, unit)
    
    # Create search variations
    search_variations = []
    
    # If it's a specific branded product, try brand + product type
    if brand:
        search_variations.append(f"{brand} {product_type}")
    
    # Try just the product type
    search_variations.append(product_type)
    
    # Try the first part of the product name
    first_part = product_name.split(',')[0].strip()
    if first_part not in search_variations:
        search_variations.append(first_part)
    
    # Add category-specific search terms
    if category == 'coffee':
        search_variations.append("coffee")
        if brand:
            search_variations.append(f"{brand} coffee")
        if 'ground' in product_name.lower():
            search_variations.append("ground coffee")
        if 'whole bean' in product_name.lower():
            search_variations.append("whole bean coffee")
    
    elif category == 'meat':
        if 'ground beef' in product_name.lower():
            search_variations.append("ground beef")
            lean_match = re.search(r'(\d+)%\s+lean', product_name, re.IGNORECASE)
            if lean_match:
                leanness = lean_match.group(1)
                search_variations.append(f"{leanness}% lean ground beef")
        elif 'chicken' in product_name.lower():
            if 'breast' in product_name.lower():
                search_variations.append("chicken breast")
            elif 'thigh' in product_name.lower():
                search_variations.append("chicken thigh")
            else:
                search_variations.append("chicken")
    
    elif category == 'snacks':
        if 'protein' in product_name.lower() and 'bar' in product_name.lower():
            search_variations.append("protein bar")
            if brand:
                search_variations.append(f"{brand} protein bar")
        elif 'bar' in product_name.lower():
            search_variations.append("nutrition bar")
            if brand:
                search_variations.append(f"{brand} bar")
    
    elif category == 'nuts':
        for nut in ['almond', 'peanut', 'cashew', 'pecan', 'walnut', 'pistachio', 'hazelnut']:
            if nut in product_name.lower():
                search_variations.append(nut)
                search_variations.append(f"{nut}s")
                if 'butter' in product_name.lower():
                    search_variations.append(f"{nut} butter")
    
    elif category == 'dairy':
        if 'yogurt' in product_name.lower():
            search_variations.append("yogurt")
            if 'greek' in product_name.lower():
                search_variations.append("greek yogurt")
        elif 'cheese' in product_name.lower():
            search_variations.append("cheese")
    
    elif category == 'eggs':
        search_variations.append("eggs")
        if 'cage free' in product_name.lower():
            search_variations.append("cage free eggs")
    
    elif category == 'pizza':
        search_variations.append("pizza")
        if 'pepperoni' in product_name.lower():
            search_variations.append("pepperoni pizza")
        elif 'cheese' in product_name.lower():
            search_variations.append("cheese pizza")
    
    elif category == 'oil':
        if 'olive' in product_name.lower():
            search_variations.append("olive oil")
            if 'extra virgin' in product_name.lower():
                search_variations.append("extra virgin olive oil")
    
    return search_variations, category

# Function to calculate match confidence score
def calculate_match_confidence(query, food_name, food_category=None, product_category=None):
    query_words = set(query.lower().split())
    food_words = set(food_name.lower().split())
    
    # Calculate word overlap
    common_words = query_words.intersection(food_words)
    if not common_words:
        return 0.1  # Very low confidence if no words match
    
    # Calculate Jaccard similarity (intersection over union)
    jaccard = len(common_words) / len(query_words.union(food_words))
    
    # Boost score if key words match
    score = jaccard
    
    # Check for exact brand match
    query_brand = extract_brand(query)
    food_brand = extract_brand(food_name)
    
    if query_brand and food_brand and query_brand.lower() == food_brand.lower():
        score += 0.3  # Big boost for brand match
    
    # Check for category match
    if food_category and product_category:
        # Define category mappings
        category_mappings = {
            'coffee': ['coffee', 'beverages'],
            'meat': ['meat', 'beef', 'pork', 'poultry'],
            'seafood': ['seafood', 'fish'],
            'nuts': ['nuts', 'nut products'],
            'dairy': ['dairy', 'milk', 'cheese', 'yogurt'],
            'eggs': ['eggs'],
            'fruits': ['fruits', 'berries'],
            'vegetables': ['vegetables'],
            'snacks': ['snacks', 'bars', 'cookies'],
            'beverages': ['beverages', 'drinks'],
            'pizza': ['pizza', 'fast food'],
            'oil': ['oil', 'fats'],
            'breakfast': ['breakfast', 'cereal']
        }
        
        # Check if food category matches product category
        food_category_lower = food_category.lower()
        for pc, fc_list in category_mappings.items():
            if product_category == pc and any(fc in food_category_lower for fc in fc_list):
                score += 0.3  # Big boost for category match
    
    # Penalize known incorrect matches
    if 'peanut' in food_name.lower() and 'peanut' not in query.lower() and product_category != 'nuts':
        score -= 0.5  # Heavy penalty for matching to peanuts when not appropriate
    
    if 'HAPPY BELLY MIX' in food_name and 'happy belly' not in query.lower():
        score -= 0.3  # Penalty for generic Happy Belly Mix match
    
    if 'BREAD CRUMBS' in food_name and 'bread' not in query.lower() and 'crumb' not in query.lower():
        score -= 0.4  # Penalty for bread crumbs as fallback
    
    return max(0.1, min(score, 1.0))  # Cap between 0.1 and 1.0

# Function to search and get nutrition data
def get_nutrition(product_name, quantity=None, unit=None):
    # Get search variations and product category
    search_variations, product_category = prepare_search_terms(product_name, quantity, unit)
    
    best_match = None
    best_confidence = 0
    
    # Try each search variation
    for search_term in search_variations:
        # Search the database
        search_url = f"{base_url}foods/search?api_key={api_key}&query={search_term}"
        try:
            response = requests.get(search_url)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('foods') and len(data['foods']) > 0:
                    # Check the top 5 results (or fewer if less available)
                    for i, food in enumerate(data['foods'][:5]):
                        food_id = food['fdcId']
                        food_name = food.get('description', '')
                        food_category = food.get('foodCategory', '')
                        
                        # Calculate match confidence
                        confidence = calculate_match_confidence(product_name, food_name, food_category, product_category)
                        
                        # Keep track of the best match
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_match = {'food_id': food_id, 'food_name': food_name, 'confidence': confidence}
        except Exception as e:
            print(f"Error searching for {search_term}: {str(e)}")
            time.sleep(1)  # Wait a bit before trying the next term
    
    # If we found a good match, get the nutrition data
    if best_match and best_match['confidence'] > 0.2:  # Minimum confidence threshold
        food_id = best_match['food_id']
        food_name = best_match['food_name']
        confidence = best_match['confidence']
        
        # Get detailed nutrition
        detail_url = f"{base_url}food/{food_id}?api_key={api_key}"
        try:
            detail_response = requests.get(detail_url)
            
            if detail_response.status_code == 200:
                detail = detail_response.json()
                
                # Extract nutrients
                calories = 0
                protein = 0
                carbs = 0
                fat = 0
                fiber = 0
                sugar = 0
                
                # Get serving size information
                serving_size = None
                serving_unit = None
                
                if 'servingSize' in detail:
                    serving_size = detail.get('servingSize')
                    serving_unit = detail.get('servingSizeUnit', '')
                elif 'foodPortions' in detail and detail['foodPortions']:
                    portion = detail['foodPortions'][0]
                    serving_size = portion.get('amount')
                    serving_unit = portion.get('measureUnit', {}).get('name', '')
                
                # Extract the values
                for nutrient in detail.get('foodNutrients', []):
                    nutrient_name = nutrient.get('nutrient', {}).get('name', '')
                    amount = nutrient.get('amount', 0)
                    
                    if 'Energy' in nutrient_name and 'kcal' in nutrient.get('nutrient', {}).get('unitName', ''):
                        calories = amount
                    elif 'Protein' in nutrient_name:
                        protein = amount
                    elif 'Carbohydrate' in nutrient_name and 'by difference' in nutrient_name:
                        carbs = amount
                    elif 'Total lipid (fat)' in nutrient_name:
                        fat = amount
                    elif 'Fiber' in nutrient_name:
                        fiber = amount
                    elif 'Sugars' in nutrient_name and 'total' in nutrient_name.lower():
                        sugar = amount
                
                return {
                    'food_id': food_id,
                    'food_name': food_name,
                    'confidence': confidence,
                    'calories': calories,
                    'protein': protein,
                    'carbs': carbs,
                    'fat': fat,
                    'fiber': fiber,
                    'sugar': sugar,
                    'serving_size': serving_size,
                    'serving_unit': serving_unit
                }
        except Exception as e:
            print(f"Error getting nutrition for {food_name}: {str(e)}")
    
    return None

# Function to process a single product
def process_product(row_data):
    idx, row = row_data
    product_name = row['Product Name']
    uid = row['UID']
    quantity = row.get('Quantity')
    unit = row.get('Unit')
    
    result = {
        'idx': idx,
        'uid': uid,
        'product_name': product_name,
        'nutrition': None,
        'log': []
    }
    
    result['log'].append(f"Processing {idx+1}/{len(df)}: {product_name[:50]}...")
    result['log'].append(f"  Quantity: {quantity} {unit}")
    
    # Get nutrition data
    nutrition = get_nutrition(product_name, quantity, unit)
    
    if nutrition:
        result['nutrition'] = nutrition
        
        serving_info = ""
        if nutrition.get('serving_size') is not None:
            serving_info = f" (per {nutrition.get('serving_size')} {nutrition.get('serving_unit')})"
        
        result['log'].append(f"  Found: {nutrition.get('food_name')} (Confidence: {nutrition.get('confidence'):.2f})")
        result['log'].append(f"  Nutrition: Calories={nutrition.get('calories')}, Protein={nutrition.get('protein')}g{serving_info}")
    else:
        result['log'].append(f"  No nutrition data found.")
    
    return result

# Function to save results to CSV
def save_results(df, usda_df):
    df.to_csv("fresh_products_with_uid.csv", index=False, lineterminator='\n')
    usda_df.to_csv("usda_nutrition_data.csv", index=False, lineterminator='\n')
    
    # Also save a backup in case of interruption
    timestamp = int(time.time())
    df.to_csv(f"backup_fresh_products_{timestamp}.csv", index=False, lineterminator='\n')
    usda_df.to_csv(f"backup_usda_data_{timestamp}.csv", index=False, lineterminator='\n')

# Main function to process all products in parallel
def main():
    global df, usda_df
    
    # Check if we have already processed some products
    if os.path.exists("usda_nutrition_data.csv"):
        try:
            existing_usda_df = pd.read_csv("usda_nutrition_data.csv")
            if len(existing_usda_df) > 0:
                print(f"Found existing data with {len(existing_usda_df)} products. Resuming from there.")
                usda_df = existing_usda_df
        except Exception as e:
            print(f"Error loading existing data: {str(e)}")
    
    # Get products that haven't been processed yet
    processed_uids = set(usda_df['UID'].values) if 'UID' in usda_df.columns else set()
    products_to_process = [(i, row) for i, row in df.iterrows() if row['UID'] not in processed_uids]
    
    print(f"Processing {len(products_to_process)} products out of {len(df)} total products")
    
    # Set the number of workers based on CPU cores (but not too many to avoid API rate limits)
    max_workers = min(10, os.cpu_count() or 4)
    print(f"Using {max_workers} parallel workers")
    
    # Process products in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_product = {executor.submit(process_product, row_data): row_data for row_data in products_to_process}
        
        # Process results as they complete
        for future in tqdm(concurrent.futures.as_completed(future_to_product), total=len(products_to_process), desc="Processing products"):
            try:
                result = future.result()
                idx = result['idx']
                uid = result['uid']
                nutrition = result['nutrition']
                
                # Print logs
                for log_line in result['log']:
                    print(log_line)
                
                # Add to USDA dataframe if nutrition data was found
                if nutrition:
                    new_row = {
                        'UID': uid,
                        'Amazon Name': result['product_name'],
                        'USDA Name': nutrition.get('food_name'),
                        'USDA Food ID': nutrition.get('food_id'),
                        'Match Confidence': nutrition.get('confidence'),
                        'Serving Size': nutrition.get('serving_size'),
                        'Serving Unit': nutrition.get('serving_unit'),
                        'Calories': nutrition.get('calories'),
                        'Protein (g)': nutrition.get('protein'),
                        'Carbs (g)': nutrition.get('carbs'),
                        'Fat (g)': nutrition.get('fat'),
                        'Fiber (g)': nutrition.get('fiber'),
                        'Sugar (g)': nutrition.get('sugar')
                    }
                    usda_df = pd.concat([usda_df, pd.DataFrame([new_row])], ignore_index=True)
                
                # Save intermediate results every 10 products
                if idx % 10 == 0:
                    save_results(df, usda_df)
                    print(f"  Saved intermediate results to CSV files")
            
            except Exception as e:
                print(f"Error processing product: {str(e)}")
    
    # Final save
    save_results(df, usda_df)
    
    print("\nDone! Results saved to:")
    print("1. fresh_products_with_uid.csv - Original data with UIDs")
    print("2. usda_nutrition_data.csv - USDA lookup data with nutrition information")

if __name__ == "__main__":
    main() 