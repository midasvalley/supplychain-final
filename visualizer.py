"""
Enhanced Visualization module for diet optimization results, including detailed charts and summary tables.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

class OptimizationVisualizer:
    def __init__(self, results, food_items):
        self.results = results
        self.food_items = food_items
        self.weeks = range(len(results['order_schedule']))

    def plot_weekly_order_volume(self):
        order_volume = []
        for week in self.weeks:
            week_order = self.results['order_schedule'][week]
            perishable_volume = sum(qty for item, qty in week_order.items() if self.food_items[item]['perishable'])
            non_perishable_volume = sum(qty for item, qty in week_order.items() if not self.food_items[item]['perishable'])
            order_volume.append({'Week': week, 'Perishable': perishable_volume, 'Non-Perishable': non_perishable_volume})

        df = pd.DataFrame(order_volume)
        fig, ax = plt.subplots(figsize=(15,6))
        df.set_index('Week').plot(kind='bar', stacked=True, alpha=0.8, ax=ax)
        plt.title('Weekly Shopping Order Volume')
        plt.ylabel('Quantity Ordered (Servings)')
        plt.xlabel('Week')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig

    def plot_consumption_vs_purchase(self):
        consumption_purchase = []
        for week in self.weeks:
            week_order = sum(self.results['order_schedule'][week].values())
            week_consumption = sum(self.results['consumption'][week].values())
            consumption_purchase.append({'Week': week, 'Ordered': week_order, 'Consumed': week_consumption})

        df = pd.DataFrame(consumption_purchase)
        fig, ax = plt.subplots(figsize=(15,6))
        df.set_index('Week').plot(kind='line', marker='o', ax=ax)
        plt.title('Weekly Consumption vs. Purchases')
        plt.ylabel('Total Quantity (Servings)')
        plt.xlabel('Week')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig

    def plot_weekly_waste(self):
        weekly_waste = []
        for week in self.weeks:
            waste = self.results['waste'][week] if week > 0 else {}  # No waste in first week
            perishable_waste = sum(qty for item, qty in waste.items() if self.food_items[item]['perishable'])
            non_perishable_waste = sum(qty for item, qty in waste.items() if not self.food_items[item]['perishable'])
            weekly_waste.append({'Week': week, 'Perishable Waste': perishable_waste, 'Non-Perishable Waste': non_perishable_waste})

        df = pd.DataFrame(weekly_waste)
        fig, ax = plt.subplots(figsize=(15,6))
        df.set_index('Week').plot(kind='bar', stacked=True, color=['salmon', 'gray'], ax=ax)
        plt.title('Weekly Waste Analysis')
        plt.ylabel('Quantity Wasted (Servings)')
        plt.xlabel('Week')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig

    def generate_summary_tables(self):
        shopping_summary = []
        consumption_waste_summary = []

        for week in self.weeks:
            order = self.results['order_schedule'][week]
            consumption = self.results['consumption'][week]
            waste = self.results['waste'][week]

            total_ordered = sum(order.values())
            total_consumed = sum(consumption.values())
            total_wasted = sum(waste.values())

            shopping_summary.append({
                'Week': week,
                'Items Ordered': len(order),
                'Quantity Ordered': total_ordered,
                'Total Cost': self.results['cost_breakdown']['weekly'][week]['items'],
                'Delivery Cost': self.results['cost_breakdown']['weekly'][week]['delivery']
            })

            consumption_waste_summary.append({
                'Week': week,
                'Items Consumed': len(consumption),
                'Quantity Consumed': total_consumed,
                'Quantity Wasted': total_wasted,
                'Waste Cost': sum(waste[item] * self.food_items[item]['cost'] for item in waste)
            })

        shopping_df = pd.DataFrame(shopping_summary)
        consumption_waste_df = pd.DataFrame(consumption_waste_summary)

        print("Shopping Summary Table:")
        print(shopping_df.to_string(index=False))

        print("\nConsumption and Waste Summary Table:")
        print(consumption_waste_df.to_string(index=False))
