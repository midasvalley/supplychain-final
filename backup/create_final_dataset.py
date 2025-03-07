import pandas as pd

def create_final_dataset():
    """
    Fix the last remaining low confidence match and create the final dataset.
    """
    # Load the data from the previous round
    try:
        df = pd.read_csv('usda_nutrition_data_final_fixed.csv')
        print(f"Loaded data with {len(df)} rows")
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return

    # Fix the last remaining low confidence match
    uid = '8a123bfc'  # Amazon Brand - Happy Belly Dark Sweet Cherries
    mask = df['UID'] == uid
    if mask.any():
        # Update the row with the fix
        fix = {
            'USDA Name': 'Cherries, sweet, raw',
            'USDA Food ID': '9070',
            'Match Confidence': 0.95
        }
        for key, value in fix.items():
            df.loc[mask, key] = value
        
        # Print the update
        row = df.loc[mask].iloc[0]
        print(f"Updated: {row['Amazon Name']} -> {row['USDA Name']} (Match Confidence: {row['Match Confidence']})")
    
    # Check if there are any remaining low confidence matches
    threshold = 0.5
    low_confidence = df[df['Match Confidence'] < threshold]
    if len(low_confidence) > 0:
        print(f"\nWarning: There are still {len(low_confidence)} items with match confidence < {threshold}")
        for _, row in low_confidence.iterrows():
            print(f"UID: {row['UID']}")
            print(f"Amazon Name: {row['Amazon Name']}")
            print(f"USDA Name: {row['USDA Name']}")
            print(f"Match Confidence: {row['Match Confidence']}")
    else:
        print("\nSuccess: All items now have match confidence >= 0.5")
    
    # Save the final dataset
    df.to_csv('usda_nutrition_data_final_complete.csv', index=False)
    print(f"Saved final dataset to usda_nutrition_data_final_complete.csv")
    
    # Generate a summary of the data quality
    print("\nData quality summary:")
    confidence_ranges = {
        '0.9-1.0': df[(df['Match Confidence'] >= 0.9) & (df['Match Confidence'] <= 1.0)].shape[0],
        '0.8-0.9': df[(df['Match Confidence'] >= 0.8) & (df['Match Confidence'] < 0.9)].shape[0],
        '0.7-0.8': df[(df['Match Confidence'] >= 0.7) & (df['Match Confidence'] < 0.8)].shape[0],
        '0.6-0.7': df[(df['Match Confidence'] >= 0.6) & (df['Match Confidence'] < 0.7)].shape[0],
        '0.5-0.6': df[(df['Match Confidence'] >= 0.5) & (df['Match Confidence'] < 0.6)].shape[0],
        '<0.5': df[df['Match Confidence'] < 0.5].shape[0]
    }
    
    for range_name, count in confidence_ranges.items():
        percentage = (count / len(df)) * 100
        print(f"Match Confidence {range_name}: {count} items ({percentage:.2f}%)")

if __name__ == "__main__":
    create_final_dataset() 