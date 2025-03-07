import requests
import time
import csv
import pandas as pd

# API configuration
base_url = "https://api.nal.usda.gov/fdc/v1/"
api_key = "hrj12UbPsq1NKRF6uePbp5FudbBatEpP3qcbIMNX"  # You'll need to replace this with your actual API key

# List of problematic items to re-query with specific search terms
problematic_items = [
    {"uid": "19a86f53", "name": "365 by Whole Foods Market Gummies Probiotic", "search_term": "probiotic gummies supplement"},
    {"uid": "e6e8bda6", "name": "Fast Twitch Energy Drink from Gatorade Orange", "search_term": "gatorade energy drink orange"},
    {"uid": "0881eed1", "name": "365 by Whole Foods Market Hometown Blend Coffee", "search_term": "coffee ground roasted"},
    {"uid": "b9e83681", "name": "McCormick Ground Cinnamon", "search_term": "ground cinnamon spice"},
    {"uid": "96e79d9c", "name": "Almond Breeze Unsweetened Original", "search_term": "almond milk unsweetened"},
    {"uid": "55264932", "name": "Fresh Blueberries 1 Pint", "search_term": "fresh blueberries raw"},
    {"uid": "71737a9a", "name": "365 by Whole Foods Market Organic Cauliflower", "search_term": "cauliflower raw organic"},
    {"uid": "95d7c912", "name": "365 by Whole Foods Market Organic Concord Grapes", "search_term": "concord grapes organic"},
    {"uid": "59d1055f", "name": "365 by Whole Foods Market Organic Granola", "search_term": "granola organic cereal"},
    {"uid": "e6280b24", "name": "365 by Whole Foods Market Pitted Dates", "search_term": "dates pitted dried"},
    {"uid": "48f76628", "name": "365 by Whole Foods Market Organic Carrots", "search_term": "carrots organic raw"},
    {"uid": "177677b9", "name": "365 by Whole Foods Market Mushrooms", "search_term": "mushrooms raw"},
    {"uid": "8a459777", "name": "Amazon Brand - Happy Belly Frozen Broccoli", "search_term": "broccoli frozen"},
    {"uid": "ee8e2275", "name": "Amazon Fresh Beef Broth", "search_term": "beef broth liquid"},
    {"uid": "a80d9e5f", "name": "Ball Park Hot Dog Buns", "search_term": "hot dog buns bread"},
    {"uid": "83de0d2f", "name": "365 by Whole Foods Market Gummies Probiotic", "search_term": "probiotic gummies supplement"},
    {"uid": "266bca6d", "name": "365 by Whole Foods Market Hometown Blend Coffee", "search_term": "coffee ground roasted"},
    {"uid": "79dfe247", "name": "Amazon Fresh Brand Original Unsweetened Almond Milk", "search_term": "almond milk unsweetened"}
]

def search_food(query):
    """Search for food items using the USDA API"""
    search_url = f"{base_url}foods/search?api_key={api_key}&query={query}"
    try:
        response = requests.get(search_url)
        if response.status_code == 200:
            data = response.json()
            if data.get('foods') and len(data['foods']) > 0:
                return data['foods'][:5]  # Return top 5 results
        return []
    except Exception as e:
        print(f"Error searching for {query}: {str(e)}")
        time.sleep(1)
        return []

def get_food_details(food_id):
    """Get detailed nutrition information for a food item"""
    detail_url = f"{base_url}food/{food_id}?api_key={api_key}"
    try:
        response = requests.get(detail_url)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error getting details for food ID {food_id}: {str(e)}")
        time.sleep(1)
        return None

def extract_nutrition(food_detail):
    """Extract nutrition information from food details"""
    if not food_detail:
        return None
    
    # Extract nutrients
    nutrients = {
        'calories': 0,
        'protein': 0,
        'carbs': 0,
        'fat': 0,
        'fiber': 0,
        'sugar': 0
    }
    
    # Get serving size information
    serving_size = None
    serving_unit = None
    
    if 'servingSize' in food_detail:
        serving_size = food_detail.get('servingSize')
        serving_unit = food_detail.get('servingSizeUnit', '')
    elif 'foodPortions' in food_detail and food_detail['foodPortions']:
        portion = food_detail['foodPortions'][0]
        serving_size = portion.get('amount')
        serving_unit = portion.get('measureUnit', {}).get('name', '')
    
    # Extract nutrient values
    if 'foodNutrients' in food_detail:
        for nutrient in food_detail['foodNutrients']:
            nutrient_id = nutrient.get('nutrient', {}).get('id')
            amount = nutrient.get('amount', 0)
            
            # Map nutrient IDs to our categories
            if nutrient_id == 1008:  # Energy (kcal)
                nutrients['calories'] = amount
            elif nutrient_id == 1003:  # Protein
                nutrients['protein'] = amount
            elif nutrient_id == 1005:  # Carbohydrates
                nutrients['carbs'] = amount
            elif nutrient_id == 1004:  # Total lipid (fat)
                nutrients['fat'] = amount
            elif nutrient_id == 1079:  # Fiber
                nutrients['fiber'] = amount
            elif nutrient_id == 2000:  # Total sugars
                nutrients['sugar'] = amount
    
    return {
        'serving_size': serving_size,
        'serving_unit': serving_unit,
        'nutrients': nutrients
    }

def requery_items():
    """Re-query problematic items and save results"""
    results = []
    
    for item in problematic_items:
        print(f"Processing: {item['name']}")
        
        # Search for the item using the specific search term
        search_results = search_food(item['search_term'])
        
        if not search_results:
            print(f"No results found for {item['search_term']}")
            continue
        
        # Process top 3 results
        item_results = []
        for i, result in enumerate(search_results[:3]):
            food_id = result['fdcId']
            food_name = result.get('description', '')
            
            print(f"  Found match: {food_name}")
            
            # Get detailed nutrition
            food_detail = get_food_details(food_id)
            nutrition = extract_nutrition(food_detail)
            
            if nutrition:
                item_results.append({
                    'uid': item['uid'],
                    'amazon_name': item['name'],
                    'usda_name': food_name,
                    'usda_food_id': food_id,
                    'rank': i + 1,
                    'serving_size': nutrition['serving_size'],
                    'serving_unit': nutrition['serving_unit'],
                    'calories': nutrition['nutrients']['calories'],
                    'protein': nutrition['nutrients']['protein'],
                    'carbs': nutrition['nutrients']['carbs'],
                    'fat': nutrition['nutrients']['fat'],
                    'fiber': nutrition['nutrients']['fiber'],
                    'sugar': nutrition['nutrients']['sugar']
                })
        
        # Add the best result to our overall results
        if item_results:
            results.append(item_results[0])  # Take the top result
    
    # Save results to CSV
    if results:
        df = pd.DataFrame(results)
        df.to_csv('requeried_items.csv', index=False)
        print(f"Saved {len(results)} requeried items to requeried_items.csv")
    else:
        print("No results to save")

if __name__ == "__main__":
    requery_items() 