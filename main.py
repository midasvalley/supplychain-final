"""
Main script to run the diet optimization and generate visualizations.
Configuration variables can be adjusted below.
"""

from diet_optimizer import DietOptimizer
from visualizer import OptimizationVisualizer
from food_data_manager import FoodDataManager
import os
import copy
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

# ============= CONFIGURATION =============

# Timeline
WEEKS = 36  # Total weeks to optimize for
START_DATE = "2024-09-29"  # Start date (YYYY-MM-DD)

# Nutritional Requirements (weekly)
CALORIES = {
    'min': 20000,  # ~2850 cal/day minimum (light training/recovery)
    'max': 28000   # ~4000 cal/day maximum (peak training volume)
}

PROTEIN = {
    'min': 700,    # ~100g/day minimum (maintenance)
    'max': 1400    # ~200g/day maximum (intense training/recovery)
}

FAT = {
    'min': 350,    # ~50g/day minimum (low-fat, higher-carb phases)
    'max': 840     # ~120g/day maximum (higher-fat endurance fueling)
}

CARBS = {
    'min': 2100,   # ~300g/day minimum (lighter weeks)
    'max': 5250    # ~750g/day maximum (peak training weeks)
}

FIBER = {
    'min': 140,    # ~20g/day minimum (minimum digestive health)
    'max': 350     # ~50g/day maximum (upper digestive comfort)
}

SUGAR = {
    'min': 0,      # No strict minimum
    'max': 700     # ~100g/day maximum (reasonable allowance for fruits/gels)
}

# Order Constraints
MIN_ORDER_VALUE = 75  # Minimum order value in dollars
DELIVERY_FEE = 10     # Delivery fee in dollars

# Default Weekly Serving Limits
DEFAULT_WEEKLY_LIMIT = 14  # Default maximum servings per week for any item

# Data Source
FOOD_CATALOG_PATH = 'food_catalog.csv'

# Output Configuration
OUTPUT_DIR = 'output'
SAVE_PLOTS = True
SAVE_CSV = True

# Solver Configuration
SOLVER_TIME_LIMIT = 900  # 15 minutes time limit
SOLVER_MIP_GAP = 0.20   # 10% optimality gap for faster convergence (increased from 5%)
SOLVER_SHOW_PROGRESS = True  # Show solver progress

# ============= END CONFIGURATION =============

def update_constraints(food_manager):
    """Update the constraints based on configuration variables."""
    # Update nutritional constraints
    nutritional_constraints = {
        'calories': CALORIES,
        'protein': PROTEIN,
        'fat': FAT,
        'carbs': CARBS,
        'fiber': FIBER,
        'sugar': SUGAR
    }
    food_manager.update_nutritional_constraints(nutritional_constraints)
    
    # Update order constraints
    order_constraints = {
        'min_order_value': MIN_ORDER_VALUE,
        'delivery_fee': DELIVERY_FEE,
        'total_weeks': WEEKS,
        'start_date': START_DATE,
        # Add solver configuration
        'solver_time_limit': SOLVER_TIME_LIMIT,
        'solver_mip_gap': SOLVER_MIP_GAP,
        'solver_show_progress': SOLVER_SHOW_PROGRESS
    }
    food_manager.update_order_constraints(order_constraints)
    
    # Update serving limits if specified
    food_items = food_manager.get_food_items()
    for item in food_items:
        # Set default weekly limit
        food_items[item]['weekly_limit'] = DEFAULT_WEEKLY_LIMIT
    
    return food_manager.get_nutritional_constraints(), food_manager.get_order_constraints(), food_items

def print_configuration(food_manager):
    """Print current configuration settings."""
    food_items = food_manager.get_food_items()
    
    print("\nCurrent Configuration:")
    print("=" * 50)
    print(f"Timeline: {WEEKS} weeks starting from {START_DATE}")
    print("\nNutritional Requirements (weekly):")
    print(f"Calories: {CALORIES['min']} - {CALORIES['max']} kcal")
    print(f"Protein:  {PROTEIN['min']} - {PROTEIN['max']} g")
    print(f"Fat:      {FAT['min']} - {FAT['max']} g")
    print(f"Carbs:    {CARBS['min']} - {CARBS['max']} g")
    print(f"Fiber:    {FIBER['min']} - {FIBER['max']} g")
    print(f"Sugar:    {SUGAR['min']} - {SUGAR['max']} g")
    print("\nOrder Constraints:")
    print(f"Minimum Order Value: ${MIN_ORDER_VALUE}")
    print(f"Delivery Fee: ${DELIVERY_FEE}")
    print(f"\nDefault Weekly Serving Limit: {DEFAULT_WEEKLY_LIMIT}")
    print("\nData Source:")
    print(f"Food Catalog: {FOOD_CATALOG_PATH}")
    print("\nOutput Configuration:")
    print(f"Output Directory: {OUTPUT_DIR}")
    print(f"Save Plots: {SAVE_PLOTS}")
    print(f"Save CSV: {SAVE_CSV}")
    
    print("\nSolver Configuration:")
    print(f"Time Limit: {SOLVER_TIME_LIMIT} seconds")
    print(f"MIP Gap: {SOLVER_MIP_GAP * 100}%")
    print(f"Show Progress: {SOLVER_SHOW_PROGRESS}")
    print("=" * 50 + "\n")

def main():
    # Initialize food data manager
    food_manager = FoodDataManager(FOOD_CATALOG_PATH)
    
    # Print current configuration
    print_configuration(food_manager)
    
    # Update constraints based on configuration
    nutritional_constraints, order_constraints, food_items = update_constraints(food_manager)
    
    # Run optimization
    print("Running diet optimization...")
    optimizer = DietOptimizer(
        food_items=food_items,
        nutritional_constraints=nutritional_constraints,
        order_constraints=order_constraints
    )
    
    # Get formatted results (this will trigger the solve operation once)
    formatted_results = optimizer.get_formatted_results()
    
    if not formatted_results:
        print("Failed to find optimal solution.")
        return
    
    # Print detailed weekly action plan
    print("\n=== WEEKLY ACTION PLAN ===")
    print("What to order and eat each week:\n")
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    print(formatted_results['weekly_schedule'].to_string())
    
    print("\n=== COST BREAKDOWN ===")
    print(formatted_results['cost_summary'].to_string())
    
    print("\n=== NUTRITIONAL SUMMARY ===")
    print(formatted_results['nutritional_summary'].to_string())
    
    if SAVE_PLOTS or SAVE_CSV:
        # Create output directory if it doesn't exist
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
            
        # Get raw results for visualization
        raw_results = optimizer.get_results()
        
        if SAVE_PLOTS:
            print("\n=== Generating Visualizations ===")
            # Transform formatted results into the structure expected by visualizer
            # Convert order schedule to use just servings instead of the full order info
            order_schedule = []
            for week_orders in raw_results['order_schedule']:
                week_dict = {}
                for item, order_info in week_orders.items():
                    week_dict[item] = order_info['servings']
                order_schedule.append(week_dict)
            
            # Calculate waste for each week
            waste_schedule = []
            for week in range(len(raw_results['order_schedule'])):
                week_waste = {}
                if week > 0:  # Can only calculate waste from second week onwards
                    prev_inventory = raw_results['inventory_levels'][week-1]
                    consumption = raw_results['consumption_schedule'][week]
                    for item in food_items:
                        if food_items[item]['perishable']:
                            prev_qty = prev_inventory.get(item, 0)
                            consumed = consumption.get(item, 0)
                            if prev_qty > consumed:
                                week_waste[item] = prev_qty - consumed
                waste_schedule.append(week_waste)
                
            visualization_results = {
                'order_schedule': order_schedule,
                'consumption': raw_results['consumption_schedule'],
                'waste': waste_schedule,
                'cost_breakdown': raw_results['cost_breakdown']
            }
            
            # Create visualizer instance with the transformed results
            visualizer = OptimizationVisualizer(visualization_results, food_items)
            
            # Create plots directory
            plots_dir = os.path.join(OUTPUT_DIR, 'plots')
            os.makedirs(plots_dir, exist_ok=True)
            
            # Save weekly order volume plot
            order_plot = visualizer.plot_weekly_order_volume()
            order_plot.savefig(os.path.join(plots_dir, 'order_volume.png'), bbox_inches='tight', dpi=300)
            plt.close(order_plot)
            print("✓ Saved order volume plot")
            
            # Save consumption vs purchase plot
            consumption_plot = visualizer.plot_consumption_vs_purchase()
            consumption_plot.savefig(os.path.join(plots_dir, 'consumption_vs_purchase.png'), bbox_inches='tight', dpi=300)
            plt.close(consumption_plot)
            print("✓ Saved consumption vs purchase plot")
            
            # Save weekly waste plot
            waste_plot = visualizer.plot_weekly_waste()
            waste_plot.savefig(os.path.join(plots_dir, 'weekly_waste.png'), bbox_inches='tight', dpi=300)
            plt.close(waste_plot)
            print("✓ Saved weekly waste plot")
            
            # Generate and save summary tables
            print("\n=== Generating Summary Tables ===")
            visualizer.generate_summary_tables()
        
        if SAVE_CSV:
            print("\n=== Saving Data Files ===")
            # Save main results
            formatted_results['weekly_schedule'].to_csv(os.path.join(OUTPUT_DIR, 'weekly_schedule.csv'))
            formatted_results['cost_summary'].to_csv(os.path.join(OUTPUT_DIR, 'cost_summary.csv'))
            formatted_results['nutritional_summary'].to_csv(os.path.join(OUTPUT_DIR, 'nutritional_summary.csv'))
            
            # Save additional detailed data
            pd.DataFrame(raw_results['order_schedule']).to_csv(os.path.join(OUTPUT_DIR, 'detailed_orders.csv'))
            pd.DataFrame(raw_results['consumption_schedule']).to_csv(os.path.join(OUTPUT_DIR, 'detailed_consumption.csv'))
            pd.DataFrame(raw_results['inventory_levels']).to_csv(os.path.join(OUTPUT_DIR, 'detailed_inventory.csv'))
            
            # Save a summary of the optimization parameters
            with open(os.path.join(OUTPUT_DIR, 'optimization_parameters.txt'), 'w') as f:
                f.write("=== Optimization Parameters ===\n\n")
                f.write(f"Timeline: {WEEKS} weeks starting from {START_DATE}\n\n")
                f.write("Nutritional Requirements (weekly):\n")
                f.write(f"Calories: {CALORIES['min']} - {CALORIES['max']} kcal\n")
                f.write(f"Protein:  {PROTEIN['min']} - {PROTEIN['max']} g\n")
                f.write(f"Fat:      {FAT['min']} - {FAT['max']} g\n")
                f.write(f"Carbs:    {CARBS['min']} - {CARBS['max']} g\n")
                f.write(f"Fiber:    {FIBER['min']} - {FIBER['max']} g\n")
                f.write(f"Sugar:    {SUGAR['min']} - {SUGAR['max']} g\n\n")
                f.write("Order Constraints:\n")
                f.write(f"Minimum Order Value: ${MIN_ORDER_VALUE}\n")
                f.write(f"Delivery Fee: ${DELIVERY_FEE}\n")
                f.write(f"Default Weekly Serving Limit: {DEFAULT_WEEKLY_LIMIT}\n")
            
            print("✓ Saved weekly schedule")
            print("✓ Saved cost summary")
            print("✓ Saved nutritional summary")
            print("✓ Saved detailed order data")
            print("✓ Saved detailed consumption data")
            print("✓ Saved detailed inventory data")
            print("✓ Saved optimization parameters")
            
        print(f"\nAll outputs have been saved to: {os.path.abspath(OUTPUT_DIR)}")

if __name__ == '__main__':
    main() 