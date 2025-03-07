import pandas as pd

def find_remaining_low_confidence():
    """
    Find items with low match confidence in the fixed USDA nutrition data.
    """
    # Load the fixed data
    try:
        df = pd.read_csv('usda_nutrition_data_fixed.csv')
        print(f"Loaded fixed data with {len(df)} rows")
    except Exception as e:
        print(f"Error loading fixed data: {str(e)}")
        return
    
    # Find items with low match confidence
    threshold = 0.5
    low_confidence = df[df['Match Confidence'] < threshold]
    
    # Sort by match confidence
    low_confidence = low_confidence.sort_values('Match Confidence')
    
    # Print the results
    print(f"\nFound {len(low_confidence)} items with match confidence < {threshold}:")
    for _, row in low_confidence.iterrows():
        print(f"UID: {row['UID']}")
        print(f"Amazon Name: {row['Amazon Name']}")
        print(f"USDA Name: {row['USDA Name']}")
        print(f"Match Confidence: {row['Match Confidence']}")
        print("-" * 80)
    
    # Save the results to a CSV file
    low_confidence.to_csv('remaining_low_confidence.csv', index=False)
    print(f"Saved {len(low_confidence)} remaining low confidence matches to remaining_low_confidence.csv")

if __name__ == "__main__":
    find_remaining_low_confidence() 