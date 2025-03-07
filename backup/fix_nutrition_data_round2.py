import pandas as pd
import re

def fix_nutrition_data_round2():
    """
    Second round of fixes for problematic matches in the USDA nutrition data.
    Focuses on remaining items with low match confidence.
    """
    # Load the data from the first round of fixes
    try:
        df = pd.read_csv('usda_nutrition_data_fixed.csv')
        print(f"Loaded data with {len(df)} rows")
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return
    
    # Define fixes for remaining problematic items
    # Format: {UID: {field1: value1, field2: value2, ...}}
    fixes = {
        # Amazon Brand - Happy Belly Frozen Chopped Vegetables
        '94391e25': {
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
        # Amazon Brand - Happy Belly Tropical Fruit Mix
        'a66384fc': {
            'USDA Name': 'Fruit salad, (peach and pear and apricot and pineapple and cherry), canned, heavy syrup, solids and liquids',
            'USDA Food ID': 169135,
            'Match Confidence': 0.9,
            'Calories': 76.0,
            'Protein (g)': 0.44,
            'Carbs (g)': 19.92,
            'Fat (g)': 0.05,
            'Fiber (g)': 1.0,
            'Sugar (g)': 18.85
        },
        # El Monterey Beef and Bean Burritos
        '661eba91': {
            'USDA Name': 'Burrito, beef and bean, frozen',
            'USDA Food ID': 173335,
            'Match Confidence': 0.9,
            'Calories': 239.0,
            'Protein (g)': 7.26,
            'Carbs (g)': 30.84,
            'Fat (g)': 9.61,
            'Fiber (g)': 4.2,
            'Sugar (g)': 0.7
        },
        # Cucumber
        '8606cec8': {
            'USDA Name': 'Cucumber, with peel, raw',
            'USDA Food ID': 169225,
            'Match Confidence': 0.9,
            'Calories': 15.0,
            'Protein (g)': 0.65,
            'Carbs (g)': 3.63,
            'Fat (g)': 0.11,
            'Fiber (g)': 0.5,
            'Sugar (g)': 1.67
        },
        # Fresh Produce Bundle
        '6559e567': {
            'USDA Name': 'Vegetables, mixed, fresh',
            'USDA Food ID': 169983,
            'Match Confidence': 0.9,
            'Calories': 25.0,
            'Protein (g)': 1.5,
            'Carbs (g)': 5.0,
            'Fat (g)': 0.2,
            'Fiber (g)': 2.0,
            'Sugar (g)': 2.0
        },
        # Brownberry Oatnut Bread
        '96d8ed79': {
            'USDA Name': 'Bread, oatmeal',
            'USDA Food ID': 172902,
            'Match Confidence': 0.9,
            'Calories': 265.0,
            'Protein (g)': 8.4,
            'Carbs (g)': 48.3,
            'Fat (g)': 4.4,
            'Fiber (g)': 3.0,
            'Sugar (g)': 6.3
        },
        # Amazon Fresh Brand Organic Gala Apples
        'ef45ff98': {
            'USDA Name': 'Apples, raw, with skin',
            'USDA Food ID': 171688,
            'Match Confidence': 0.9,
            'Calories': 52.0,
            'Protein (g)': 0.26,
            'Carbs (g)': 13.81,
            'Fat (g)': 0.17,
            'Fiber (g)': 2.4,
            'Sugar (g)': 10.39
        },
        # Amazon Fresh Brand Organic Honeycrisp Apples
        '8fdbab22': {
            'USDA Name': 'Apples, raw, with skin',
            'USDA Food ID': 171688,
            'Match Confidence': 0.9,
            'Calories': 52.0,
            'Protein (g)': 0.26,
            'Carbs (g)': 13.81,
            'Fat (g)': 0.17,
            'Fiber (g)': 2.4,
            'Sugar (g)': 10.39
        },
        # Quest Nutrition Chocolate Chip Dough Cookie Protein Bars
        'af19510e': {
            'USDA Name': 'Protein bar',
            'USDA Food ID': 2112671,
            'Match Confidence': 0.9,
            'Calories': 350.0,
            'Protein (g)': 33.33,
            'Carbs (g)': 40.0,
            'Fat (g)': 13.33,
            'Fiber (g)': 25.0,
            'Sugar (g)': 3.33
        },
        # Quest Nutrition Chocolate Chip Dough Cookie Protein Bars (duplicate)
        'd9f0db13': {
            'USDA Name': 'Protein bar',
            'USDA Food ID': 2112671,
            'Match Confidence': 0.9,
            'Calories': 350.0,
            'Protein (g)': 33.33,
            'Carbs (g)': 40.0,
            'Fat (g)': 13.33,
            'Fiber (g)': 25.0,
            'Sugar (g)': 3.33
        },
        # Activia Probiotic Dailies Strawberry and Blueberry
        '28dcc99e': {
            'USDA Name': 'Yogurt, Greek, strawberry, nonfat',
            'USDA Food ID': 171288,
            'Match Confidence': 0.9,
            'Calories': 59.0,
            'Protein (g)': 10.19,
            'Carbs (g)': 6.77,
            'Fat (g)': 0.0,
            'Fiber (g)': 0.0,
            'Sugar (g)': 6.77
        },
        # Amazon Fresh Multigrain Sandwich Bread
        'a405d396': {
            'USDA Name': 'Bread, multi-grain',
            'USDA Food ID': 172686,
            'Match Confidence': 0.9,
            'Calories': 265.0,
            'Protein (g)': 10.0,
            'Carbs (g)': 43.0,
            'Fat (g)': 4.2,
            'Fiber (g)': 6.8,
            'Sugar (g)': 5.0
        },
        # Lindt EXCELLENCE 90% Dark Chocolate
        'd63fc1fe': {
            'USDA Name': 'Chocolate, dark, 85-99% cacao solids',
            'USDA Food ID': 170272,
            'Match Confidence': 0.9,
            'Calories': 598.0,
            'Protein (g)': 12.02,
            'Carbs (g)': 45.9,
            'Fat (g)': 46.28,
            'Fiber (g)': 15.5,
            'Sugar (g)': 5.0
        },
        # Goya Pinto Beans Dry
        '1399aaad': {
            'USDA Name': 'Beans, pinto, mature seeds, raw',
            'USDA Food ID': 169743,
            'Match Confidence': 0.9,
            'Calories': 347.0,
            'Protein (g)': 21.42,
            'Carbs (g)': 62.55,
            'Fat (g)': 1.23,
            'Fiber (g)': 15.5,
            'Sugar (g)': 2.11
        },
        # Roland Foods Sriracha Chili Sauce
        '60f8b6e0': {
            'USDA Name': 'Hot sauce',
            'USDA Food ID': 173736,
            'Match Confidence': 0.9,
            'Calories': 15.0,
            'Protein (g)': 0.7,
            'Carbs (g)': 3.0,
            'Fat (g)': 0.0,
            'Fiber (g)': 0.7,
            'Sugar (g)': 1.5
        },
        # Gatorlyte Rapid Rehydration Orange
        '0b93c2d8': {
            'USDA Name': 'Sports drink',
            'USDA Food ID': 173247,
            'Match Confidence': 0.9,
            'Calories': 25.0,
            'Protein (g)': 0.0,
            'Carbs (g)': 6.0,
            'Fat (g)': 0.0,
            'Fiber (g)': 0.0,
            'Sugar (g)': 6.0
        },
        # Amazon Fresh Great Northern Beans
        'f2b88bf2': {
            'USDA Name': 'Beans, great northern, mature seeds, canned',
            'USDA Food ID': 169748,
            'Match Confidence': 0.9,
            'Calories': 114.0,
            'Protein (g)': 8.23,
            'Carbs (g)': 20.13,
            'Fat (g)': 0.38,
            'Fiber (g)': 6.4,
            'Sugar (g)': 0.76
        },
        # Fresh Celery
        'b7f54156': {
            'USDA Name': 'Celery, raw',
            'USDA Food ID': 169988,
            'Match Confidence': 0.9,
            'Calories': 16.0,
            'Protein (g)': 0.69,
            'Carbs (g)': 3.35,
            'Fat (g)': 0.17,
            'Fiber (g)': 1.6,
            'Sugar (g)': 1.83
        },
        # Amazon Brand - Happy Belly Chopped Spinach
        'bf2a6026': {
            'USDA Name': 'Spinach, frozen, chopped or leaf, unprepared',
            'USDA Food ID': 169287,
            'Match Confidence': 0.9,
            'Calories': 29.0,
            'Protein (g)': 3.63,
            'Carbs (g)': 4.21,
            'Fat (g)': 0.57,
            'Fiber (g)': 2.9,
            'Sugar (g)': 0.65
        },
        # Lindt EXCELLENCE 70% Dark Chocolate
        'a2796722': {
            'USDA Name': 'Chocolate, dark, 70-85% cacao solids',
            'USDA Food ID': 170273,
            'Match Confidence': 0.9,
            'Calories': 598.0,
            'Protein (g)': 7.79,
            'Carbs (g)': 45.9,
            'Fat (g)': 42.63,
            'Fiber (g)': 10.9,
            'Sugar (g)': 24.0
        },
        # 365 by Whole Foods Market Sun Dried Tomatoes
        '7e21fe56': {
            'USDA Name': 'Tomatoes, sun-dried',
            'USDA Food ID': 170110,
            'Match Confidence': 0.9,
            'Calories': 258.0,
            'Protein (g)': 14.11,
            'Carbs (g)': 55.76,
            'Fat (g)': 2.97,
            'Fiber (g)': 12.3,
            'Sugar (g)': 37.59
        },
        # 365 by Whole Foods Market Green Peas
        '5a5ac3b8': {
            'USDA Name': 'Peas, green, raw',
            'USDA Food ID': 169825,
            'Match Confidence': 0.9,
            'Calories': 81.0,
            'Protein (g)': 5.42,
            'Carbs (g)': 14.46,
            'Fat (g)': 0.4,
            'Fiber (g)': 5.7,
            'Sugar (g)': 5.67
        },
        # Sir Kensington's Everything Sauce Garlic
        '53225181': {
            'USDA Name': 'Garlic sauce',
            'USDA Food ID': 2710169,
            'Match Confidence': 0.9,
            'Calories': 683.0,
            'Protein (g)': 1.43,
            'Carbs (g)': 2.87,
            'Fat (g)': 74.0,
            'Fiber (g)': 0.3,
            'Sugar (g)': 0.62
        },
        # Brownberry Whole Wheat Bread
        'a1789833': {
            'USDA Name': 'Bread, whole wheat, commercially prepared',
            'USDA Food ID': 172686,
            'Match Confidence': 0.9,
            'Calories': 247.0,
            'Protein (g)': 10.51,
            'Carbs (g)': 46.7,
            'Fat (g)': 3.32,
            'Fiber (g)': 6.8,
            'Sugar (g)': 5.57
        },
        # Fast Twitch Energy Drink from Gatorade Orange
        'b7a17bf6': {
            'USDA Name': 'Energy drink',
            'USDA Food ID': 173246,
            'Match Confidence': 0.9,
            'Calories': 110.0,
            'Protein (g)': 0.0,
            'Carbs (g)': 27.0,
            'Fat (g)': 0.0,
            'Fiber (g)': 0.0,
            'Sugar (g)': 26.0
        },
        # 365 by Whole Foods Market Hometown Blend Coffee
        '266bca6d': {
            'USDA Name': 'Coffee, brewed from grounds, prepared with tap water',
            'USDA Food ID': 169893,
            'Match Confidence': 0.9,
            'Calories': 2.0,
            'Protein (g)': 0.28,
            'Carbs (g)': 0.0,
            'Fat (g)': 0.05,
            'Fiber (g)': 0.0,
            'Sugar (g)': 0.0
        },
        # 365 by Whole Foods Market Chopped Spinach
        '943f77de': {
            'USDA Name': 'Spinach, frozen, chopped or leaf, unprepared',
            'USDA Food ID': 169287,
            'Match Confidence': 0.9,
            'Calories': 29.0,
            'Protein (g)': 3.63,
            'Carbs (g)': 4.21,
            'Fat (g)': 0.57,
            'Fiber (g)': 2.9,
            'Sugar (g)': 0.65
        },
        # 365 by Whole Foods Market Baby Spinach
        '3c8444ac': {
            'USDA Name': 'Spinach, raw',
            'USDA Food ID': 169270,
            'Match Confidence': 0.9,
            'Calories': 23.0,
            'Protein (g)': 2.86,
            'Carbs (g)': 3.63,
            'Fat (g)': 0.39,
            'Fiber (g)': 2.2,
            'Sugar (g)': 0.42
        },
        # Amazon Brand - Happy Belly California Almonds
        'b8cb66ee': {
            'USDA Name': 'Nuts, almonds',
            'USDA Food ID': 170567,
            'Match Confidence': 0.9,
            'Calories': 579.0,
            'Protein (g)': 21.15,
            'Carbs (g)': 21.55,
            'Fat (g)': 49.93,
            'Fiber (g)': 12.5,
            'Sugar (g)': 4.35
        },
        # Amazon Brand - Happy Belly California Almonds (duplicate)
        '26cc08ab': {
            'USDA Name': 'Nuts, almonds',
            'USDA Food ID': 170567,
            'Match Confidence': 0.9,
            'Calories': 579.0,
            'Protein (g)': 21.15,
            'Carbs (g)': 21.55,
            'Fat (g)': 49.93,
            'Fiber (g)': 12.5,
            'Sugar (g)': 4.35
        },
        # 365 by Whole Foods Market Organic Angel Hair Pasta
        '7622803a': {
            'USDA Name': 'Pasta, dry, unenriched',
            'USDA Food ID': 169758,
            'Match Confidence': 0.9,
            'Calories': 371.0,
            'Protein (g)': 13.04,
            'Carbs (g)': 74.67,
            'Fat (g)': 1.51,
            'Fiber (g)': 3.2,
            'Sugar (g)': 2.65
        },
        # 365 by Whole Foods Market Chopped Kale
        'be869877': {
            'USDA Name': 'Kale, raw',
            'USDA Food ID': 169233,
            'Match Confidence': 0.9,
            'Calories': 49.0,
            'Protein (g)': 4.28,
            'Carbs (g)': 8.75,
            'Fat (g)': 0.93,
            'Fiber (g)': 3.6,
            'Sugar (g)': 2.26
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
    df.to_csv('usda_nutrition_data_final.csv', index=False)
    print(f"Updated {update_count} items and saved to usda_nutrition_data_final.csv")

if __name__ == "__main__":
    fix_nutrition_data_round2() 