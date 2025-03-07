"""
Food data manager responsible for loading and managing food catalog data.
"""
import pandas as pd
from typing import Dict, Any
import os

class FoodDataManager:
    def __init__(self, csv_path: str = 'food_catalog_temp.csv'):
        self.csv_path = csv_path
        self.food_items = {}
        self.nutritional_constraints = {}
        self.order_constraints = {}
        self.reload_data()
    
    def reload_data(self) -> None:
        """Reload data from CSV file."""
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"CSV file not found at {self.csv_path}")
        
        df = pd.read_csv(self.csv_path)
        self.food_items = {}
        
        for _, row in df.iterrows():
            # Convert price per serving from string to float
            price_per_serving = float(row['Price per serving'].replace('$', '').strip())
            
            food_item = {
                'name': row['Product Name'],
                'cost': price_per_serving,
                'calories': row['Calories'],
                'protein': row['Protein (g)'],
                'fat': row['Fat (g)'],
                'carbs': row['Carbs (g)'],
                'fiber': row['Fiber (g)'],
                'sugar': row['Sugar (g)'],
                'perishable': row['Perishable'] == 'Y',
                'package_size': row['Package Size'],
                'weekly_limit': 14  # Default weekly limit if not specified
            }
            
            # Create a snake_case key from the product name
            key = row['Product Name'].lower().replace(' ', '_').replace('(', '').replace(')', '')
            self.food_items[key] = food_item
    
    def get_food_items(self) -> Dict[str, Dict[str, Any]]:
        """Return the current food items dictionary."""
        return self.food_items
    
    def get_nutritional_constraints(self) -> Dict[str, Dict[str, float]]:
        """Return the current nutritional constraints."""
        return self.nutritional_constraints
    
    def get_order_constraints(self) -> Dict[str, Any]:
        """Return the current order constraints."""
        return self.order_constraints
    
    def update_nutritional_constraints(self, new_constraints: Dict[str, Dict[str, float]]) -> None:
        """Update nutritional constraints."""
        self.nutritional_constraints = new_constraints
    
    def update_order_constraints(self, new_constraints: Dict[str, Any]) -> None:
        """Update order constraints."""
        self.order_constraints = new_constraints 