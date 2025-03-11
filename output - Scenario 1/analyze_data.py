import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import re
from datetime import datetime

# Set style for better visualizations
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def load_data():
    """Load all relevant CSV files"""
    script_dir = Path(__file__).parent
    nutrition_df = pd.read_csv(script_dir / 'nutritional_summary.csv')
    
    # Convert Week to datetime if it's in date format, otherwise keep as is
    try:
        nutrition_df['Week'] = pd.to_datetime(nutrition_df['Week'])
    except:
        pass  # Keep original format if conversion fails
        
    return nutrition_df

def extract_food_data(nutrition_df):
    """Extract food data from the nutrition dataframe"""
    inventory_data = {}
    consumption_data = {}
    wastage_data = {}
    order_data = {}
    
    for _, row in nutrition_df.iterrows():
        week = row['Week']
        if isinstance(week, str) and 'TOTAL' in week:
            continue
            
        # Parse inventory
        if isinstance(row['Remaining Inventory'], str):
            inventory_items = re.findall(r'(\w+(?:_\w+)*): (\d+) servings', row['Remaining Inventory'])
            if week not in inventory_data:
                inventory_data[week] = {}
            for item, amount in inventory_items:
                inventory_data[week][item] = int(amount)
        
        # Parse consumption
        if isinstance(row['Consumption Plan'], str):
            consumption_items = re.findall(r'(\w+(?:_\w+)*): (\d+) servings', row['Consumption Plan'])
            if week not in consumption_data:
                consumption_data[week] = {}
            for item, amount in consumption_items:
                consumption_data[week][item] = int(amount)
        
        # Parse wastage
        if isinstance(row['Wastage'], str) and row['Wastage'] != 'None':
            wastage_items = re.findall(r'(\w+(?:_\w+)*): (\d+) servings', row['Wastage'])
            if week not in wastage_data:
                wastage_data[week] = {}
            for item, amount in wastage_items:
                wastage_data[week][item] = int(amount)
        
        # Parse orders
        if isinstance(row['Orders'], str) and row['Orders'] != 'No orders needed':
            order_items = re.findall(r'(\w+(?:_\w+)*): (\d+) servings', row['Orders'])
            if week not in order_data:
                order_data[week] = {}
            for item, amount in order_items:
                order_data[week][item] = int(amount)
    
    return inventory_data, consumption_data, wastage_data, order_data

def get_top_items(inventory_data, n=5):
    """Get top n items based on average inventory"""
    item_totals = {}
    for week_data in inventory_data.values():
        for item, amount in week_data.items():
            if item not in item_totals:
                item_totals[item] = []
            item_totals[item].append(amount)
    
    item_averages = {item: sum(amounts)/len(amounts) for item, amounts in item_totals.items()}
    return sorted(item_averages.items(), key=lambda x: x[1], reverse=True)[:n]

def visualize_inventory_over_time(inventory_data):
    """Create a line chart showing inventory levels over time for top 5 items"""
    top_items = get_top_items(inventory_data)
    weeks = sorted(inventory_data.keys())
    
    plt.figure(figsize=(12, 6))
    for item, _ in top_items:
        inventory_levels = [inventory_data[week].get(item, 0) for week in weeks]
        plt.plot(weeks, inventory_levels, marker='o', label=item.replace('_', ' ').title())
    
    plt.title('Inventory Levels Over Time (Top 5 Items)', fontsize=14, pad=15)
    plt.xlabel('Week', fontsize=12)
    plt.ylabel('Inventory (Servings)', fontsize=12)
    plt.xticks(rotation=45)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    script_dir = Path(__file__).parent
    plt.savefig(script_dir / 'plots/inventory_over_time.png', dpi=300, bbox_inches='tight')
    plt.close()

def visualize_consumption_and_waste(consumption_data, wastage_data):
    """Create visualizations for consumption and wastage patterns"""
    # Calculate total consumption
    total_consumption = {}
    for week_data in consumption_data.values():
        for item, amount in week_data.items():
            total_consumption[item] = total_consumption.get(item, 0) + amount
    
    # Calculate total wastage
    total_wastage = {}
    for week_data in wastage_data.values():
        for item, amount in week_data.items():
            total_wastage[item] = total_wastage.get(item, 0) + amount
    
    # Get top 10 items by consumption
    sorted_items = sorted(total_consumption.items(), key=lambda x: x[1], reverse=True)
    top_10 = sorted_items[:10]
    others_consumption = sum(amount for _, amount in sorted_items[10:])
    
    # Prepare data for plotting
    items = [item.replace('_', ' ').title() for item, _ in top_10]
    consumption_values = [amount for _, amount in top_10]
    wastage_values = [total_wastage.get(item, 0) for item, _ in top_10]
    
    # Create consumption pie chart
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    labels = [f"{item}: {amount/sum(total_consumption.values())*100:.1f}%" 
             for item, amount in zip(items, consumption_values)]
    if others_consumption > 0:
        consumption_values.append(others_consumption)
        labels.append(f"Others: {others_consumption/sum(total_consumption.values())*100:.1f}%")
    
    plt.pie(consumption_values, labels=labels, autopct='%1.1f%%', startangle=90)
    plt.title('Total Consumption Distribution', fontsize=14, pad=15)
    
    # Create stacked bar chart for consumption vs wastage
    plt.subplot(1, 2, 2)
    x = range(len(items))
    plt.bar(x, consumption_values[:len(items)], label='Consumed', color='#2ecc71')
    plt.bar(x, wastage_values, bottom=consumption_values[:len(items)], 
            label='Wasted', color='#e74c3c', alpha=0.7)
    
    plt.title('Consumption vs Wastage by Item', fontsize=14, pad=15)
    plt.xlabel('Items', fontsize=12)
    plt.ylabel('Servings', fontsize=12)
    plt.xticks(x, items, rotation=45, ha='right')
    plt.legend()
    
    plt.tight_layout()
    script_dir = Path(__file__).parent
    plt.savefig(script_dir / 'plots/consumption_and_waste.png', dpi=300, bbox_inches='tight')
    plt.close()

def visualize_total_inventory_orders(inventory_data, nutrition_df):
    """Create a line chart of total inventory with order indicators"""
    weeks = sorted(inventory_data.keys())
    total_inventory = [sum(inventory_data[week].values()) for week in weeks]
    
    plt.figure(figsize=(12, 6))
    plt.plot(weeks, total_inventory, marker='o', label='Total Inventory')
    
    # Add order indicators
    for week in weeks:
        orders = nutrition_df[nutrition_df['Week'] == week]['Orders'].iloc[0]
        if orders != 'No orders needed':
            plt.axvline(x=week, color='red', linestyle='--', alpha=0.3)
    
    plt.title('Total Inventory with Order Indicators', fontsize=14, pad=15)
    plt.xlabel('Week', fontsize=12)
    plt.ylabel('Total Inventory (Servings)', fontsize=12)
    plt.xticks(rotation=45)
    plt.legend(['Total Inventory', 'Order Placed'])
    plt.tight_layout()
    
    script_dir = Path(__file__).parent
    plt.savefig(script_dir / 'plots/total_inventory_with_orders.png', dpi=300, bbox_inches='tight')
    plt.close()

def visualize_item_specific_analysis(inventory_data, consumption_data, wastage_data, order_data):
    """Create detailed analysis for top 3 items"""
    top_items = get_top_items(inventory_data, n=3)
    weeks = sorted(inventory_data.keys())
    
    for item, _ in top_items:
        plt.figure(figsize=(12, 6))
        
        # Plot inventory
        inventory_levels = [inventory_data[week].get(item, 0) for week in weeks]
        plt.plot(weeks, inventory_levels, marker='o', label='Inventory', color='blue')
        
        # Plot consumption
        consumption_levels = [consumption_data[week].get(item, 0) for week in weeks]
        plt.plot(weeks, consumption_levels, marker='s', label='Consumption', color='green')
        
        # Plot wastage
        wastage_levels = [wastage_data.get(week, {}).get(item, 0) for week in weeks]
        plt.plot(weeks, wastage_levels, marker='^', label='Wastage', color='red')
        
        # Add order indicators
        for week in weeks:
            if week in order_data and item in order_data[week]:
                plt.axvline(x=week, color='purple', linestyle='--', alpha=0.3)
        
        plt.title(f'{item.replace("_", " ").title()} - Detailed Analysis', fontsize=14, pad=15)
        plt.xlabel('Week', fontsize=12)
        plt.ylabel('Servings', fontsize=12)
        plt.xticks(rotation=45)
        plt.legend(['Inventory', 'Consumption', 'Wastage', 'Order Placed'])
        plt.tight_layout()
        
        script_dir = Path(__file__).parent
        plt.savefig(script_dir / f'plots/{item}_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()

def main():
    script_dir = Path(__file__).parent
    (script_dir / 'plots').mkdir(exist_ok=True)
    
    # Load data
    nutrition_df = load_data()
    inventory_data, consumption_data, wastage_data, order_data = extract_food_data(nutrition_df)
    
    # Generate visualizations
    visualize_inventory_over_time(inventory_data)
    visualize_consumption_and_waste(consumption_data, wastage_data)
    visualize_total_inventory_orders(inventory_data, nutrition_df)
    visualize_item_specific_analysis(inventory_data, consumption_data, wastage_data, order_data)
    
    print("Analysis complete! Check the 'plots' directory for the following visualizations:")
    print("1. inventory_over_time.png - Line chart showing inventory levels for top 5 items")
    print("2. consumption_and_waste.png - Consumption distribution and wastage comparison")
    print("3. total_inventory_with_orders.png - Total inventory levels with order indicators")
    print("4. [item]_analysis.png - Detailed analysis for top 3 items")

if __name__ == "__main__":
    main()