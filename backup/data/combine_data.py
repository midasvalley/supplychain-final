import csv
import re

# Function to convert units
def standardize_units(purchase_qty, purchase_unit, serving_size, serving_unit):
    # Convert all units to lowercase for easier comparison
    purchase_unit = purchase_unit.lower() if purchase_unit else ""
    serving_unit = serving_unit.lower() if serving_unit else ""
    
    # Standardize unit names
    unit_mapping = {
        "count": "count",
        "lb": "g",
        "pound": "g",
        "pounds": "g",
        "oz": "g",
        "ounce": "g",
        "ounces": "g",
        "g": "g",
        "grm": "g",
        "gram": "g",
        "grams": "g",
        "ml": "ml",
        "mlt": "ml",
        "milliliter": "ml",
        "milliliters": "ml",
        "each": "count"
    }
    
    # Standardize purchase unit
    if purchase_unit in unit_mapping:
        std_purchase_unit = unit_mapping[purchase_unit]
    else:
        std_purchase_unit = purchase_unit
    
    # Standardize serving unit
    if serving_unit in unit_mapping:
        std_serving_unit = unit_mapping[serving_unit]
    else:
        std_serving_unit = serving_unit
    
    # If serving unit is missing or undetermined, use purchase unit if available
    if not serving_unit or serving_unit == "undetermined":
        std_serving_unit = std_purchase_unit
        if serving_size == "":
            serving_size = "1"  # Default serving size
    
    # Convert quantities to the same unit
    try:
        purchase_qty = float(purchase_qty) if purchase_qty else 0
        serving_size = float(serving_size) if serving_size else 0
        
        # Convert lb to g (1 lb = 453.592 g)
        if purchase_unit == "lb" and std_purchase_unit == "g":
            purchase_qty = purchase_qty * 453.592
        
        # Convert oz to g (1 oz = 28.3495 g)
        if purchase_unit == "oz" and std_purchase_unit == "g":
            purchase_qty = purchase_qty * 28.3495
        
        # If purchase unit is "count" and serving unit is weight-based (g)
        # Assume 1 count = serving_size of the weight unit
        if purchase_unit == "count" and std_serving_unit == "g" and serving_size > 0:
            purchase_qty = purchase_qty * serving_size
            std_purchase_unit = "g"
    except (ValueError, TypeError):
        # If conversion fails, keep original values
        pass
    
    return purchase_qty, std_purchase_unit, serving_size, std_serving_unit

# Read product data
products = {}
with open('fresh_products_with_uid.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        uid = row['UID']
        # Remove $ from price
        price = row['Price'].replace('$', '')
        products[uid] = {
            'Product Name': row['Product Name'],
            'Price': price,
            'Purchase Quantity': row['Quantity'],
            'Purchase Unit': row['Unit']
        }

# Read nutrition data
nutrition = {}
with open('usda_nutrition_data.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        uid = row['UID']
        nutrition[uid] = {
            'Serving Size': row['Serving Size'],
            'Serving Unit': row['Serving Unit'],
            'Calories': row['Calories'],
            'Protein (g)': row['Protein (g)'],
            'Carbs (g)': row['Carbs (g)'],
            'Fat (g)': row['Fat (g)'],
            'Fiber (g)': row['Fiber (g)'],
            'Sugar (g)': row['Sugar (g)']
        }

# Combine data and write to new CSV
with open('combined_product_nutrition_data.csv', 'w', newline='', encoding='utf-8') as f:
    # Define the header
    header = ['Product Name', 'Price', 'Purchase Quantity', 'Purchase Unit',
              'Serving Size', 'Serving Unit', 'Calories', 'Protein (g)',
              'Carbs (g)', 'Fat (g)', 'Fiber (g)', 'Sugar (g)']
    
    # Create a writer and write the header
    writer = csv.DictWriter(f, fieldnames=header)
    writer.writeheader()
    
    for uid, product in products.items():
        if uid in nutrition:
            # Get nutrition data for this product
            nutri_data = nutrition[uid]
            
            # Standardize units
            purchase_qty, purchase_unit, serving_size, serving_unit = standardize_units(
                product['Purchase Quantity'],
                product['Purchase Unit'],
                nutri_data['Serving Size'],
                nutri_data['Serving Unit']
            )
            
            # Format numeric values to 2 decimal places
            try:
                purchase_qty = f"{float(purchase_qty):.2f}" if purchase_qty else ""
                serving_size = f"{float(serving_size):.2f}" if serving_size else ""
                
                # Format nutrition values to 2 decimal places
                calories = f"{float(nutri_data['Calories']):.2f}" if nutri_data['Calories'] else "0.00"
                protein = f"{float(nutri_data['Protein (g)']):.2f}" if nutri_data['Protein (g)'] else "0.00"
                carbs = f"{float(nutri_data['Carbs (g)']):.2f}" if nutri_data['Carbs (g)'] else "0.00"
                fat = f"{float(nutri_data['Fat (g)']):.2f}" if nutri_data['Fat (g)'] else "0.00"
                fiber = f"{float(nutri_data['Fiber (g)']):.2f}" if nutri_data['Fiber (g)'] else "0.00"
                sugar = f"{float(nutri_data['Sugar (g)']):.2f}" if nutri_data['Sugar (g)'] else "0.00"
            except (ValueError, TypeError):
                # If conversion fails, use original values
                calories = nutri_data['Calories']
                protein = nutri_data['Protein (g)']
                carbs = nutri_data['Carbs (g)']
                fat = nutri_data['Fat (g)']
                fiber = nutri_data['Fiber (g)']
                sugar = nutri_data['Sugar (g)']
            
            # Create combined row
            row = {
                'Product Name': product['Product Name'],
                'Price': product['Price'],
                'Purchase Quantity': purchase_qty,
                'Purchase Unit': purchase_unit,
                'Serving Size': serving_size,
                'Serving Unit': serving_unit,
                'Calories': calories,
                'Protein (g)': protein,
                'Carbs (g)': carbs,
                'Fat (g)': fat,
                'Fiber (g)': fiber,
                'Sugar (g)': sugar
            }
            
            writer.writerow(row)

print("Combined data has been written to combined_product_nutrition_data.csv") 