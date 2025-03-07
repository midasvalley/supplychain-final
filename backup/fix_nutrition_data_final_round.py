import pandas as pd
import re

def fix_nutrition_data_final_round():
    """
    Fix the remaining problematic matches in the USDA nutrition data by replacing them
    with more appropriate generic food descriptions.
    """
    # Load the data from the previous round
    try:
        df = pd.read_csv('usda_nutrition_data_final.csv')
        print(f"Loaded data with {len(df)} rows")
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return

    # Dictionary of fixes for specific items by UID
    fixes = {
        # Ground beef items
        'e6d97a04': {
            'USDA Name': 'Beef, ground, 80% lean meat / 20% fat, raw',
            'USDA Food ID': '13568',
            'Match Confidence': 0.95
        },
        'f4532afc': {
            'USDA Name': 'Beef, ground, 80% lean meat / 20% fat, raw',
            'USDA Food ID': '13568',
            'Match Confidence': 0.95
        },
        
        # Happy Belly fruit items incorrectly matched to juice
        '8894650f': {  # Happy Belly Dried Cranberries
            'USDA Name': 'Cranberries, dried, sweetened',
            'USDA Food ID': '9079',
            'Match Confidence': 0.95
        },
        'aef72e60': {  # Happy Belly Red Raspberries
            'USDA Name': 'Raspberries, raw',
            'USDA Food ID': '9302',
            'Match Confidence': 0.95
        },
        'f566aa9e': {  # Happy Belly Whole Blackberries
            'USDA Name': 'Blackberries, raw',
            'USDA Food ID': '9042',
            'Match Confidence': 0.95
        },
        '3df471c0': {  # Happy Belly Sliced Peaches
            'USDA Name': 'Peaches, raw',
            'USDA Food ID': '9236',
            'Match Confidence': 0.95
        },
        'acfb15ba': {  # Happy Belly Whole Blueberries
            'USDA Name': 'Blueberries, raw',
            'USDA Food ID': '9050',
            'Match Confidence': 0.95
        },
        'c1ee01b4': {  # Happy Belly Sliced Strawberries
            'USDA Name': 'Strawberries, raw',
            'USDA Food ID': '9316',
            'Match Confidence': 0.95
        },
        '78e26c2a': {  # Happy Belly Frozen Edamame
            'USDA Name': 'Edamame, frozen, prepared',
            'USDA Food ID': '11212',
            'Match Confidence': 0.95
        },
        
        # Chia seeds
        '66646094': {  # Amazon Fresh Organic Black Chia Seeds
            'USDA Name': 'Seeds, chia seeds, dried',
            'USDA Food ID': '12006',
            'Match Confidence': 0.95
        },
        
        # Clementines
        '63ecd01f': {  # Mandarin Clementines
            'USDA Name': 'Tangerines, (mandarin oranges), raw',
            'USDA Food ID': '9218',
            'Match Confidence': 0.95
        },
        
        # Cheese items
        '28039bb7': {  # Amazon Fresh Classic Crust 4 Cheese
            'USDA Name': 'Pizza, cheese topping, regular crust, frozen, cooked',
            'USDA Food ID': '21299',
            'Match Confidence': 0.95
        },
        '6fb7726a': {  # Happy Belly Swiss Cheese Block
            'USDA Name': 'Cheese, swiss',
            'USDA Food ID': '1040',
            'Match Confidence': 0.95
        },
        
        # Pasta
        'a02a5418': {  # Pasta 16 Oz
            'USDA Name': 'Pasta, dry, enriched',
            'USDA Food ID': '20120',
            'Match Confidence': 0.95
        },
        
        # Green beans
        '3d9a7fc9': {  # 365 by Whole Foods Market Organic Green Beans
            'USDA Name': 'Beans, snap, green, raw',
            'USDA Food ID': '11052',
            'Match Confidence': 0.95
        },
        
        # Olives
        '810973a7': {  # 365 by Whole Foods Market Green Olives
            'USDA Name': 'Olives, green',
            'USDA Food ID': '9195',
            'Match Confidence': 0.95
        },
        
        # Chocolate bar
        '13db8aa5': {  # Lindt Excellence Sea Salt Bar
            'USDA Name': 'Candies, dark chocolate',
            'USDA Food ID': '19081',
            'Match Confidence': 0.95
        },
        
        # Banana
        '211fd724': {  # Banana Bunch
            'USDA Name': 'Bananas, raw',
            'USDA Food ID': '9040',
            'Match Confidence': 0.95
        }
    }

    # Apply fixes
    items_updated = 0
    for uid, fix in fixes.items():
        # Find the row with the matching UID
        mask = df['UID'] == uid
        if mask.any():
            # Update the row with the fix
            for key, value in fix.items():
                df.loc[mask, key] = value
            
            # Print the update
            row = df.loc[mask].iloc[0]
            print(f"Updated: {row['Amazon Name']} -> {row['USDA Name']} (Match Confidence: {row['Match Confidence']})")
            items_updated += 1

    # Save the updated data
    df.to_csv('usda_nutrition_data_final_fixed.csv', index=False)
    print(f"\nTotal items updated: {items_updated}")
    print(f"Saved updated data to usda_nutrition_data_final_fixed.csv")

if __name__ == "__main__":
    fix_nutrition_data_final_round() 