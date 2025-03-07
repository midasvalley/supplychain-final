import pandas as pd

def update_nutrition_data():
    """
    Update the original nutrition data CSV with the requeried items
    """
    # Load the original data
    try:
        original_df = pd.read_csv('usda_nutrition_data.csv')
        print(f"Loaded original data with {len(original_df)} rows")
    except Exception as e:
        print(f"Error loading original data: {str(e)}")
        return
    
    # Load the requeried data
    try:
        requeried_df = pd.read_csv('requeried_items.csv')
        print(f"Loaded requeried data with {len(requeried_df)} rows")
    except Exception as e:
        print(f"Error loading requeried data: {str(e)}")
        return
    
    # Create a copy of the original dataframe
    updated_df = original_df.copy()
    
    # Update rows with requeried data
    update_count = 0
    for _, row in requeried_df.iterrows():
        uid = row['uid']
        
        # Find the matching row in the original data
        mask = updated_df['UID'] == uid
        if mask.any():
            # Update the row with new data
            updated_df.loc[mask, 'USDA Name'] = row['usda_name']
            updated_df.loc[mask, 'USDA Food ID'] = row['usda_food_id']
            updated_df.loc[mask, 'Match Confidence'] = 0.9  # High confidence for manually verified matches
            
            # Update nutrition data if available
            if pd.notna(row['serving_size']):
                updated_df.loc[mask, 'Serving Size'] = row['serving_size']
            if pd.notna(row['serving_unit']):
                updated_df.loc[mask, 'Serving Unit'] = row['serving_unit']
            if pd.notna(row['calories']):
                updated_df.loc[mask, 'Calories'] = row['calories']
            if pd.notna(row['protein']):
                updated_df.loc[mask, 'Protein (g)'] = row['protein']
            if pd.notna(row['carbs']):
                updated_df.loc[mask, 'Carbs (g)'] = row['carbs']
            if pd.notna(row['fat']):
                updated_df.loc[mask, 'Fat (g)'] = row['fat']
            if pd.notna(row['fiber']):
                updated_df.loc[mask, 'Fiber (g)'] = row['fiber']
            if pd.notna(row['sugar']):
                updated_df.loc[mask, 'Sugar (g)'] = row['sugar']
            
            update_count += 1
            print(f"Updated: {row['amazon_name']} -> {row['usda_name']}")
    
    # Save the updated data
    updated_df.to_csv('usda_nutrition_data_updated.csv', index=False)
    print(f"Updated {update_count} items and saved to usda_nutrition_data_updated.csv")

if __name__ == "__main__":
    update_nutrition_data() 