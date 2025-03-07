import pandas as pd
import re

def fix_nutrition_data():
    """
    Fix problematic matches in the USDA nutrition data by replacing them with more
    appropriate generic food descriptions.
    """
    # Load the original data
    try:
        df = pd.read_csv('usda_nutrition_data.csv')
        print(f"Loaded data with {len(df)} rows")
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return
    
    # Define fixes for problematic items
    # Format: {UID: {field1: value1, field2: value2, ...}}
    fixes = {
        # Happy Belly Pecan Halves
        '652fc447': {
            'USDA Name': 'Pecans, raw',
            'USDA Food ID': 170178,  # Generic pecan ID
            'Match Confidence': 0.9,
            'Calories': 691.0,
            'Protein (g)': 9.17,
            'Carbs (g)': 13.86,
            'Fat (g)': 71.97,
            'Fiber (g)': 9.6,
            'Sugar (g)': 3.97
        },
        # Amazon Brand - Happy Belly Pecan Halves (duplicate)
        '41d8a91c': {
            'USDA Name': 'Pecans, raw',
            'USDA Food ID': 170178,
            'Match Confidence': 0.9,
            'Calories': 691.0,
            'Protein (g)': 9.17,
            'Carbs (g)': 13.86,
            'Fat (g)': 71.97,
            'Fiber (g)': 9.6,
            'Sugar (g)': 3.97
        },
        # Amazon Fresh Beef Broth
        'ee8e2275': {
            'USDA Name': 'Beef broth, ready-to-serve',
            'USDA Food ID': 173793,
            'Match Confidence': 0.9,
            'Calories': 17.0,
            'Protein (g)': 2.55,
            'Carbs (g)': 0.85,
            'Fat (g)': 0.43,
            'Fiber (g)': 0.0,
            'Sugar (g)': 0.0
        },
        # Amazon Brand - Happy Belly Frozen Broccoli
        '8a459777': {
            'USDA Name': 'Broccoli, frozen, unprepared',
            'USDA Food ID': 169967,
            'Match Confidence': 0.9,
            'Calories': 28.0,
            'Protein (g)': 2.81,
            'Carbs (g)': 5.84,
            'Fat (g)': 0.34,
            'Fiber (g)': 2.6,
            'Sugar (g)': 1.1
        },
        # Amazon Brand - Happy Belly Mixed Vegetables
        'e86e739d': {
            'USDA Name': 'Mixed vegetables, frozen, unprepared',
            'USDA Food ID': 169984,
            'Match Confidence': 0.9,
            'Calories': 81.0,
            'Protein (g)': 4.24,
            'Carbs (g)': 18.48,
            'Fat (g)': 0.22,
            'Fiber (g)': 4.0,
            'Sugar (g)': 2.93
        },
        # Amazon Brand - Happy Belly Frozen California Blend
        '207e4032': {
            'USDA Name': 'Vegetables, mixed, frozen, unprepared',
            'USDA Food ID': 169984,
            'Match Confidence': 0.9,
            'Calories': 81.0,
            'Protein (g)': 4.24,
            'Carbs (g)': 18.48,
            'Fat (g)': 0.22,
            'Fiber (g)': 4.0,
            'Sugar (g)': 2.93
        },
        # Amazon Brand - Happy Belly Green Peas
        '0532348c': {
            'USDA Name': 'Peas, green, frozen, unprepared',
            'USDA Food ID': 169827,
            'Match Confidence': 0.9,
            'Calories': 77.0,
            'Protein (g)': 5.01,
            'Carbs (g)': 13.72,
            'Fat (g)': 0.4,
            'Fiber (g)': 4.4,
            'Sugar (g)': 4.99
        },
        # Amazon Brand - Happy Belly Frozen Green Beans
        '5d4871ae': {
            'USDA Name': 'Beans, snap, green, frozen, unprepared',
            'USDA Food ID': 169809,
            'Match Confidence': 0.9,
            'Calories': 31.0,
            'Protein (g)': 1.51,
            'Carbs (g)': 6.97,
            'Fat (g)': 0.22,
            'Fiber (g)': 2.7,
            'Sugar (g)': 2.26
        },
        # 365 by Whole Foods Market Organic Carrots
        '48f76628': {
            'USDA Name': 'Carrots, raw',
            'USDA Food ID': 169975,
            'Match Confidence': 0.9,
            'Calories': 41.0,
            'Protein (g)': 0.93,
            'Carbs (g)': 9.58,
            'Fat (g)': 0.24,
            'Fiber (g)': 2.8,
            'Sugar (g)': 4.74
        },
        # 365 by Whole Foods Market Organic Cauliflower
        '71737a9a': {
            'USDA Name': 'Cauliflower, raw',
            'USDA Food ID': 169986,
            'Match Confidence': 0.9,
            'Calories': 25.0,
            'Protein (g)': 1.92,
            'Carbs (g)': 4.97,
            'Fat (g)': 0.28,
            'Fiber (g)': 2.0,
            'Sugar (g)': 1.91
        },
        # 365 by Whole Foods Market Mushrooms
        '177677b9': {
            'USDA Name': 'Mushrooms, white, raw',
            'USDA Food ID': 169890,
            'Match Confidence': 0.9,
            'Calories': 22.0,
            'Protein (g)': 3.09,
            'Carbs (g)': 3.26,
            'Fat (g)': 0.34,
            'Fiber (g)': 1.0,
            'Sugar (g)': 1.98
        },
        # Amazon Brand - Happy Belly Frozen Cauliflower
        'fb00c334': {
            'USDA Name': 'Cauliflower, frozen, unprepared',
            'USDA Food ID': 169987,
            'Match Confidence': 0.9,
            'Calories': 24.0,
            'Protein (g)': 1.84,
            'Carbs (g)': 4.68,
            'Fat (g)': 0.45,
            'Fiber (g)': 2.5,
            'Sugar (g)': 2.0
        },
        # 365 by Whole Foods Market Pitted Dates
        'e6280b24': {
            'USDA Name': 'Dates, medjool',
            'USDA Food ID': 167746,
            'Match Confidence': 0.9,
            'Calories': 277.0,
            'Protein (g)': 1.81,
            'Carbs (g)': 74.97,
            'Fat (g)': 0.15,
            'Fiber (g)': 6.7,
            'Sugar (g)': 66.47
        },
        # 365 by Whole Foods Market Organic Concord Grapes
        '95d7c912': {
            'USDA Name': 'Grapes, red or green (European type, such as Thompson seedless), raw',
            'USDA Food ID': 169106,
            'Match Confidence': 0.9,
            'Calories': 69.0,
            'Protein (g)': 0.72,
            'Carbs (g)': 18.1,
            'Fat (g)': 0.16,
            'Fiber (g)': 0.9,
            'Sugar (g)': 15.48
        },
        # 365 by Whole Foods Market Organic Granola
        '59d1055f': {
            'USDA Name': 'Granola, homemade',
            'USDA Food ID': 173979,
            'Match Confidence': 0.9,
            'Calories': 489.0,
            'Protein (g)': 10.41,
            'Carbs (g)': 63.91,
            'Fat (g)': 22.68,
            'Fiber (g)': 7.2,
            'Sugar (g)': 24.96
        },
        # Amazon Fresh Brand Original Unsweetened Almond Milk
        '79dfe247': {
            'USDA Name': 'Almond milk, unsweetened, shelf stable',
            'USDA Food ID': 1097540,
            'Match Confidence': 0.9,
            'Calories': 29.0,
            'Protein (g)': 1.01,
            'Carbs (g)': 1.04,
            'Fat (g)': 2.5,
            'Fiber (g)': 0.5,
            'Sugar (g)': 0.0
        },
        # Almond Breeze Unsweetened Original
        '96e79d9c': {
            'USDA Name': 'Almond milk, unsweetened, shelf stable',
            'USDA Food ID': 1097540,
            'Match Confidence': 0.9,
            'Calories': 29.0,
            'Protein (g)': 1.01,
            'Carbs (g)': 1.04,
            'Fat (g)': 2.5,
            'Fiber (g)': 0.5,
            'Sugar (g)': 0.0
        },
        # Ball Park Hot Dog Buns
        'a80d9e5f': {
            'USDA Name': 'Rolls, hot dog, plain',
            'USDA Food ID': 172905,
            'Match Confidence': 0.9,
            'Calories': 280.0,
            'Protein (g)': 7.0,
            'Carbs (g)': 52.0,
            'Fat (g)': 4.0,
            'Fiber (g)': 2.0,
            'Sugar (g)': 6.0
        },
        # Fresh Blueberries 1 Pint
        '55264932': {
            'USDA Name': 'Blueberries, raw',
            'USDA Food ID': 171711,
            'Match Confidence': 0.9,
            'Calories': 57.0,
            'Protein (g)': 0.74,
            'Carbs (g)': 14.49,
            'Fat (g)': 0.33,
            'Fiber (g)': 2.4,
            'Sugar (g)': 9.96
        }
    }
    
    # Apply fixes
    update_count = 0
    for uid, fix_data in fixes.items():
        # Find the matching row in the dataframe
        mask = df['UID'] == uid
        if mask.any():
            # Update the row with fix data
            for field, value in fix_data.items():
                df.loc[mask, field] = value
            
            update_count += 1
            print(f"Updated: {df.loc[mask, 'Amazon Name'].values[0]} -> {fix_data['USDA Name']}")
    
    # Save the updated data
    df.to_csv('usda_nutrition_data_fixed.csv', index=False)
    print(f"Updated {update_count} items and saved to usda_nutrition_data_fixed.csv")

if __name__ == "__main__":
    fix_nutrition_data() 