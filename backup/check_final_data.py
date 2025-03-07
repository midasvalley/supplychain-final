import pandas as pd

def check_final_data():
    """
    Check the final USDA nutrition data for any remaining low confidence matches
    and provide a summary of the fixes made.
    """
    # Load the original data
    try:
        original_df = pd.read_csv('usda_nutrition_data.csv')
        print(f"Loaded original data with {len(original_df)} rows")
    except Exception as e:
        print(f"Error loading original data: {str(e)}")
        return
    
    # Load the final data
    try:
        final_df = pd.read_csv('usda_nutrition_data_final.csv')
        print(f"Loaded final data with {len(final_df)} rows")
    except Exception as e:
        print(f"Error loading final data: {str(e)}")
        return
    
    # Count low confidence matches in original data
    original_threshold = 0.5
    original_low_confidence = original_df[original_df['Match Confidence'] < original_threshold]
    print(f"\nOriginal data had {len(original_low_confidence)} items with match confidence < {original_threshold}")
    
    # Count low confidence matches in final data
    final_threshold = 0.5
    final_low_confidence = final_df[final_df['Match Confidence'] < final_threshold]
    print(f"Final data has {len(final_low_confidence)} items with match confidence < {final_threshold}")
    
    # Calculate improvement
    improvement = len(original_low_confidence) - len(final_low_confidence)
    improvement_percentage = (improvement / len(original_low_confidence)) * 100
    print(f"Fixed {improvement} items ({improvement_percentage:.2f}% of low confidence matches)")
    
    # Print remaining low confidence matches
    if len(final_low_confidence) > 0:
        print("\nRemaining low confidence matches:")
        for _, row in final_low_confidence.iterrows():
            print(f"UID: {row['UID']}")
            print(f"Amazon Name: {row['Amazon Name']}")
            print(f"USDA Name: {row['USDA Name']}")
            print(f"Match Confidence: {row['Match Confidence']}")
            print("-" * 80)
    
    # Save the remaining low confidence matches to a CSV file
    if len(final_low_confidence) > 0:
        final_low_confidence.to_csv('remaining_low_confidence_final.csv', index=False)
        print(f"Saved {len(final_low_confidence)} remaining low confidence matches to remaining_low_confidence_final.csv")

if __name__ == "__main__":
    check_final_data() 