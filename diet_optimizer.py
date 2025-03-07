"""
Diet optimization model using PuLP to minimize total cost while meeting nutritional constraints.
Optimized for Apple Silicon with parallel processing.
"""

import pulp
import pandas as pd
import numpy as np
import platform
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
import os
import time
import sys
from datetime import datetime, timedelta

class DietOptimizer:
    def __init__(self, food_items, nutritional_constraints, order_constraints):
        """
        Initialize the diet optimizer with custom constraints.
        
        Args:
            food_items (dict): Dictionary of food items and their attributes
            nutritional_constraints (dict): Dictionary of nutritional constraints
            order_constraints (dict): Dictionary of order constraints
        """
        self.food_items = food_items
        self.nutritional_constraints = nutritional_constraints
        self.order_constraints = order_constraints
        self._has_solved = False  # Flag to track if we've already solved
        self._solution_status = None  # Store the solution status
        self.show_progress = order_constraints.get('solver_show_progress', True)
        
        # Set up parallel processing
        self.num_cores = mp.cpu_count()
        
        # Configure solver based on architecture
        if platform.processor() == 'arm':
            # For Apple Silicon, use HiGHS solver
            try:
                # Import highspy only when needed
                import highspy
                self.solver = pulp.PULP_CBC_CMD(
                    msg=False,  # Disable verbose progress messages
                    timeLimit=order_constraints.get('solver_time_limit', 900),
                    threads=self.num_cores,
                    gapRel=order_constraints.get('solver_mip_gap', 0.05),
                    options=['highs']  # Use HiGHS as the underlying solver
                )
                print("Using CBC with HiGHS backend optimized for Apple Silicon")
            except Exception as e:
                print(f"Warning: Could not initialize HiGHS solver ({e}). Using standard CBC.")
                self.solver = pulp.PULP_CBC_CMD(
                    msg=False,  # Disable verbose progress messages
                    timeLimit=order_constraints.get('solver_time_limit', 900),
                    threads=self.num_cores,
                    gapRel=order_constraints.get('solver_mip_gap', 0.05)
                )
        else:
            # For Intel processors
            self.solver = pulp.PULP_CBC_CMD(
                msg=False,  # Disable verbose progress messages
                timeLimit=order_constraints.get('solver_time_limit', 300),
                threads=True,
                gapRel=order_constraints.get('solver_mip_gap', 0.01)
            )
        
        self.model = pulp.LpProblem("Diet_Optimization", pulp.LpMinimize)
        self.weeks = range(order_constraints['total_weeks'])
        self.items = food_items.keys()
        
        # Decision Variables
        print("Creating decision variables...")
        with ThreadPoolExecutor(max_workers=self.num_cores) as executor:
            futures = [
                executor.submit(self._create_order_variables),
                executor.submit(self._create_eat_variables),
                executor.submit(self._create_order_week_variables),
                executor.submit(self._create_inventory_variables),
                executor.submit(self._create_package_variables)
            ]
            
            self.order_vars = futures[0].result()
            self.eat_vars = futures[1].result()
            self.order_week = futures[2].result()
            self.inventory = futures[3].result()
            self.package_vars = futures[4].result()
        
        # Set up the model
        print("Setting up optimization model...")
        self._setup_objective_function()
        self._setup_constraints()
        
        # Configure solver parameters for better performance
        print(f"Configuring solver to use {self.num_cores} cores...")
        os.environ['OMP_NUM_THREADS'] = str(self.num_cores)
        os.environ['MKL_NUM_THREADS'] = str(self.num_cores)
        os.environ['OPENBLAS_NUM_THREADS'] = str(self.num_cores)
        
        # Additional solver configuration for better convergence
        self.model.setSolver(self.solver)
    
    def _create_order_variables(self):
        """Create variables for ordering food items each week."""
        return pulp.LpVariable.dicts(
            "order",
            ((w, i) for w in self.weeks for i in self.items),
            lowBound=0,
            cat='Integer'
        )
    
    def _create_eat_variables(self):
        """Create variables for eating food items each week."""
        return pulp.LpVariable.dicts(
            "eat",
            ((w, i) for w in self.weeks for i in self.items),
            lowBound=0,
            cat='Integer'
        )
    
    def _create_order_week_variables(self):
        """Create binary variables indicating if an order is placed in a week."""
        return pulp.LpVariable.dicts(
            "order_week",
            self.weeks,
            cat='Binary'
        )
    
    def _create_inventory_variables(self):
        """Create variables tracking inventory levels."""
        return pulp.LpVariable.dicts(
            "inventory",
            ((w, i) for w in self.weeks for i in self.items),
            lowBound=0,
            cat='Integer'
        )
    
    def _create_package_variables(self):
        """Create variables for number of packages ordered of each item per week."""
        return pulp.LpVariable.dicts(
            "packages",
            ((w, i) for w in self.weeks for i in self.items),
            lowBound=0,
            cat='Integer'
        )
    
    def _setup_objective_function(self):
        """Set up the objective function to minimize total cost."""
        # Cost of food items
        item_costs = pulp.lpSum(
            self.order_vars[w, i] * self.food_items[i]['cost']
            for w in self.weeks
            for i in self.items
        )
        
        # Delivery fees
        delivery_costs = pulp.lpSum(
            self.order_week[w] * self.order_constraints['delivery_fee']
            for w in self.weeks
        )
        
        self.model += item_costs + delivery_costs
    
    def _setup_constraints(self):
        """Set up all constraints for the optimization model."""
        # Set up constraints in parallel
        with ThreadPoolExecutor(max_workers=self.num_cores) as executor:
            futures = [
                executor.submit(self._add_inventory_constraints),
                executor.submit(self._add_nutritional_constraints),
                executor.submit(self._add_order_constraints),
                executor.submit(self._add_serving_limit_constraints),
                executor.submit(self._add_perishable_constraints),
                executor.submit(self._add_package_size_constraints)
            ]
            # Wait for all constraints to be added
            for future in futures:
                future.result()
    
    def _add_inventory_constraints(self):
        """Add constraints for inventory tracking and balance."""
        # Initial inventory is zero
        for i in self.items:
            self.model += self.inventory[0, i] == self.order_vars[0, i]
        
        # Inventory balance constraints
        for w in self.weeks[1:]:
            for i in self.items:
                if self.food_items[i]['perishable']:
                    # Perishable items: new inventory is just what was ordered
                    self.model += self.inventory[w, i] == self.order_vars[w, i]
                else:
                    # Non-perishable items: previous inventory + orders - consumption
                    self.model += (self.inventory[w, i] == 
                                 self.inventory[w-1, i] + 
                                 self.order_vars[w, i] - 
                                 self.eat_vars[w-1, i])
        
        # No final inventory constraint - cost minimization will handle waste
    
    def _add_nutritional_constraints(self):
        """Add weekly nutritional requirement constraints."""
        for w in self.weeks:
            # Calories
            self.model += pulp.lpSum(
                self.eat_vars[w, i] * self.food_items[i]['calories']
                for i in self.items
            ) >= self.nutritional_constraints['calories']['min']
            
            self.model += pulp.lpSum(
                self.eat_vars[w, i] * self.food_items[i]['calories']
                for i in self.items
            ) <= self.nutritional_constraints['calories']['max']
            
            # Protein
            self.model += pulp.lpSum(
                self.eat_vars[w, i] * self.food_items[i]['protein']
                for i in self.items
            ) >= self.nutritional_constraints['protein']['min']
            
            self.model += pulp.lpSum(
                self.eat_vars[w, i] * self.food_items[i]['protein']
                for i in self.items
            ) <= self.nutritional_constraints['protein']['max']
            
            # Fat
            self.model += pulp.lpSum(
                self.eat_vars[w, i] * self.food_items[i]['fat']
                for i in self.items
            ) >= self.nutritional_constraints['fat']['min']
            
            self.model += pulp.lpSum(
                self.eat_vars[w, i] * self.food_items[i]['fat']
                for i in self.items
            ) <= self.nutritional_constraints['fat']['max']
            
            # Carbs
            self.model += pulp.lpSum(
                self.eat_vars[w, i] * self.food_items[i]['carbs']
                for i in self.items
            ) >= self.nutritional_constraints['carbs']['min']
            
            self.model += pulp.lpSum(
                self.eat_vars[w, i] * self.food_items[i]['carbs']
                for i in self.items
            ) <= self.nutritional_constraints['carbs']['max']
            
            # Fiber
            self.model += pulp.lpSum(
                self.eat_vars[w, i] * self.food_items[i]['fiber']
                for i in self.items
            ) >= self.nutritional_constraints['fiber']['min']
            
            self.model += pulp.lpSum(
                self.eat_vars[w, i] * self.food_items[i]['fiber']
                for i in self.items
            ) <= self.nutritional_constraints['fiber']['max']
            
            # Sugar
            self.model += pulp.lpSum(
                self.eat_vars[w, i] * self.food_items[i]['sugar']
                for i in self.items
            ) >= self.nutritional_constraints['sugar']['min']
            
            self.model += pulp.lpSum(
                self.eat_vars[w, i] * self.food_items[i]['sugar']
                for i in self.items
            ) <= self.nutritional_constraints['sugar']['max']
    
    def _add_order_constraints(self):
        """Add constraints related to ordering."""
        # Minimum order value constraint
        for w in self.weeks:
            self.model += pulp.lpSum(
                self.order_vars[w, i] * self.food_items[i]['cost']
                for i in self.items
            ) >= self.order_constraints['min_order_value'] * self.order_week[w]
            
            # Link order variables to order_week
            for i in self.items:
                self.model += self.order_vars[w, i] <= 1000 * self.order_week[w]
    
    def _add_serving_limit_constraints(self):
        """Add weekly serving limit constraints."""
        for w in self.weeks:
            for i in self.items:
                self.model += self.eat_vars[w, i] <= self.food_items[i]['weekly_limit']
    
    def _add_perishable_constraints(self):
        """Add constraints for perishable items."""
        for w in self.weeks:
            for i in self.items:
                if self.food_items[i]['perishable']:
                    # Must eat perishable items in the same week
                    self.model += self.eat_vars[w, i] == self.order_vars[w, i]
    
    def _add_package_size_constraints(self):
        """Add constraints to ensure orders are in multiples of package sizes."""
        for w in self.weeks:
            for i in self.items:
                # Link order quantities to number of packages
                self.model += self.order_vars[w, i] == (
                    self.package_vars[w, i] * self.food_items[i]['package_size']
                )
    
    def solve(self):
        """Solve the optimization model."""
        # If we already have a solution, return the cached status silently
        if self._has_solved:
            return self._solution_status
            
        print(f"\nSolving optimization model using {self.num_cores} cores...")
        print(f"Solver: {self.solver.__class__.__name__}")
        
        # Start time for progress tracking
        start_time = time.time()
        time_limit = self.order_constraints.get('solver_time_limit', 900)
        
        # Show a simple progress indicator if progress display is enabled
        if self.show_progress:
            print("Solving optimization problem...")
            
            # Variable to control the progress indicator thread
            solving_in_progress = [True]  # Using a list for mutable reference
            
            def progress_indicator():
                progress_chars = 40  # Width of the progress bar
                try:
                    while solving_in_progress[0]:
                        elapsed = time.time() - start_time
                        if elapsed >= time_limit:
                            break
                            
                        # Calculate progress based on elapsed time vs time limit
                        progress = min(elapsed / time_limit, 1.0)
                        filled = int(progress_chars * progress)
                        
                        # Update progress bar
                        sys.stdout.write("\r[" + "=" * filled + " " * (progress_chars - filled) + 
                                        f"] {elapsed:.1f}s / {time_limit:.1f}s")
                        sys.stdout.flush()
                        time.sleep(0.5)
                except Exception as e:
                    print(f"\nProgress indicator error: {e}")
            
            # Start progress indicator in a separate thread
            with ThreadPoolExecutor(max_workers=1) as executor:
                progress_future = executor.submit(progress_indicator)
                
                try:
                    # Solve the model in the main thread
                    status = self.model.solve(self.solver)
                finally:
                    # Signal the progress thread to stop
                    solving_in_progress[0] = False
                
                # Wait for progress thread to finish
                try:
                    progress_future.result(timeout=1.0)
                except:
                    pass
                
            # Complete the progress bar
            elapsed = time.time() - start_time
            sys.stdout.write("\r[" + "=" * 40 + f"] Completed in {elapsed:.1f}s          \n")
            sys.stdout.flush()
        else:
            # Just solve without progress indicator
            status = self.model.solve(self.solver)
        
        # Cache the solution status and mark as solved BEFORE printing results
        self._has_solved = True
        self._solution_status = status == pulp.LpStatusOptimal
        
        # Print the final status
        if self._solution_status:
            print(f"Found optimal solution with objective value: ${pulp.value(self.model.objective):.2f}")
        else:
            print("Failed to find optimal solution")
        
        return self._solution_status
    
    def get_results(self):
        """Get the optimization results."""
        if not self.solve():
            return None
        
        results = {
            'order_schedule': self._get_order_schedule(),
            'consumption_schedule': self._get_consumption_schedule(),
            'inventory_levels': self._get_inventory_levels(),
            'cost_breakdown': self._get_cost_breakdown()
        }
        return results
    
    def _get_order_schedule(self):
        """Get the weekly order schedule."""
        orders = []
        for w in self.weeks:
            week_orders = {}
            for i in self.items:
                qty = self.order_vars[w, i].value()
                if qty > 0:
                    week_orders[i] = {
                        'servings': int(qty),
                        'packages': int(self.package_vars[w, i].value())
                    }
            orders.append(week_orders)
        return orders
    
    def _get_consumption_schedule(self):
        """Get the weekly consumption schedule."""
        consumption = []
        for w in self.weeks:
            week_consumption = {}
            for i in self.items:
                qty = self.eat_vars[w, i].value()
                if qty > 0:
                    week_consumption[i] = int(qty)
            consumption.append(week_consumption)
        return consumption
    
    def _get_inventory_levels(self):
        """Get the weekly inventory levels."""
        inventory = []
        for w in self.weeks:
            week_inventory = {}
            for i in self.items:
                qty = self.inventory[w, i].value()
                if qty > 0:
                    week_inventory[i] = int(qty)
            inventory.append(week_inventory)
        return inventory
    
    def _get_cost_breakdown(self):
        """Get the weekly cost breakdown."""
        costs = []
        total_cost = 0
        for w in self.weeks:
            week_cost = {
                'items': sum(
                    self.order_vars[w, i].value() * self.food_items[i]['cost']
                    for i in self.items
                ),
                'delivery': (
                    self.order_constraints['delivery_fee']
                    if self.order_week[w].value() > 0.5
                    else 0
                )
            }
            week_cost['total'] = week_cost['items'] + week_cost['delivery']
            total_cost += week_cost['total']
            costs.append(week_cost)
        
        return {
            'weekly': costs,
            'total': total_cost
        }

    def get_formatted_results(self):
        """Generate formatted tables and summaries of the optimization results."""
        # Use the solve method which will now use the cached result
        if not self.solve():
            return None
        
        # Get raw results
        results = self.get_results()
        
        # Generate date range for weeks
        start_date = self.order_constraints.get('start_date', datetime.now())
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        dates = [start_date + timedelta(weeks=w) for w in self.weeks]
        date_strs = [d.strftime('%Y-%m-%d') for d in dates]
        
        formatted_results = {
            'weekly_schedule': self._format_weekly_schedule(results, date_strs),
            'cost_summary': self._format_cost_summary(results, date_strs),
            'nutritional_summary': self._format_nutritional_summary(results, date_strs)
        }
        
        return formatted_results
    
    def _format_weekly_schedule(self, results, date_strs):
        """Format the weekly schedule into a pandas DataFrame."""
        # Initialize lists to store data
        rows = []
        
        for week, date in enumerate(date_strs):
            orders = results['order_schedule'][week]
            consumption = results['consumption_schedule'][week]
            inventory = results['inventory_levels'][week]
            
            for item in self.items:
                order_info = orders.get(item, {'servings': 0, 'packages': 0})
                # For the final week, any remaining inventory is considered waste
                final_inventory = inventory.get(item, 0)
                if week == len(self.weeks) - 1 and final_inventory > 0:
                    row = {
                        'Week': date,
                        'Item': item,
                        'Order (Servings)': order_info['servings'],
                        'Order (Packages)': order_info['packages'],
                        'Consumption': consumption.get(item, 0),
                        'Inventory': 0,  # Set to 0 since all remaining inventory is waste
                        'Perishable': 'Yes' if self.food_items[item]['perishable'] else 'No',
                        'Cost per Serving': f"${self.food_items[item]['cost']:.2f}",
                        'Final Week Waste': final_inventory
                    }
                else:
                    row = {
                        'Week': date,
                        'Item': item,
                        'Order (Servings)': order_info['servings'],
                        'Order (Packages)': order_info['packages'],
                        'Consumption': consumption.get(item, 0),
                        'Inventory': inventory.get(item, 0),
                        'Perishable': 'Yes' if self.food_items[item]['perishable'] else 'No',
                        'Cost per Serving': f"${self.food_items[item]['cost']:.2f}"
                    }
                rows.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(rows)
        
        # Sort and format
        df = df.sort_values(['Week', 'Item'])
        
        return df
    
    def _format_cost_summary(self, results, date_strs):
        """Format the cost breakdown into a pandas DataFrame."""
        costs = results['cost_breakdown']['weekly']
        
        rows = []
        for week, (date, cost) in enumerate(zip(date_strs, costs)):
            row = {
                'Week': date,
                'Item Costs': f"${cost['items']:.2f}",
                'Delivery Fee': f"${cost['delivery']:.2f}",
                'Total Cost': f"${cost['total']:.2f}"
            }
            rows.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(rows)
        
        # Add total row
        total_row = {
            'Week': 'TOTAL',
            'Item Costs': f"${sum(c['items'] for c in costs):.2f}",
            'Delivery Fee': f"${sum(c['delivery'] for c in costs):.2f}",
            'Total Cost': f"${results['cost_breakdown']['total']:.2f}"
        }
        df = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)
        
        return df
    
    def _format_nutritional_summary(self, results, date_strs):
        """Format the nutritional information into a pandas DataFrame."""
        rows = []
        
        for week, date in enumerate(date_strs):
            orders = results['order_schedule'][week]
            consumption = results['consumption_schedule'][week]
            inventory = results['inventory_levels'][week]
            
            # Calculate wastage for perishable items
            wastage = {}
            if week > 0:  # Can only calculate wastage from second week onwards
                prev_inventory = results['inventory_levels'][week-1]
                for item in self.items:
                    if self.food_items[item]['perishable']:
                        # Wastage = previous inventory - consumption
                        prev_qty = prev_inventory.get(item, 0)
                        consumed = consumption.get(item, 0)
                        if prev_qty > consumed:
                            wastage[item] = prev_qty - consumed
            
            # For the final week, add any remaining inventory to waste
            if week == len(self.weeks) - 1:
                for item in self.items:
                    final_inventory = inventory.get(item, 0)
                    if final_inventory > 0:
                        wastage[item] = wastage.get(item, 0) + final_inventory
            
            # Only include items that need to be ordered, consumed, or have wastage this week
            active_items = set()
            for item in self.items:
                if (item in orders and orders[item]['servings'] > 0) or \
                   (item in consumption and consumption[item] > 0) or \
                   (item in wastage and wastage[item] > 0):
                    active_items.add(item)
            
            if active_items:  # Only add weeks where there's activity
                order_text = []
                consume_text = []
                inventory_text = []
                wastage_text = []
                
                for item in sorted(active_items):
                    # Add order information if there's an order this week
                    if item in orders and orders[item]['servings'] > 0:
                        pkg_text = f"({orders[item]['packages']} packages)" if orders[item]['packages'] > 1 else "(1 package)"
                        order_text.append(f"{item}: {orders[item]['servings']} servings {pkg_text}")
                    
                    # Add consumption information
                    if item in consumption and consumption[item] > 0:
                        consume_text.append(f"{item}: {consumption[item]} servings")
                    
                    # Add inventory information
                    if item in inventory and inventory[item] > 0:
                        inventory_text.append(f"{item}: {inventory[item]} servings")
                    
                    # Add wastage information
                    if item in wastage and wastage[item] > 0:
                        wastage_text.append(f"{item}: {wastage[item]} servings")
                
                row = {
                    'Week': date,
                    'Orders': '\n'.join(order_text) if order_text else "No orders needed",
                    'Consumption Plan': '\n'.join(consume_text),
                    'Remaining Inventory': '\n'.join(inventory_text) if inventory_text else "None",
                    'Wastage': '\n'.join(wastage_text) if wastage_text else "None",
                    'Total Cost': f"${results['cost_breakdown']['weekly'][week]['total']:.2f}"
                }
                rows.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(rows)
        
        # Calculate total wastage
        total_wastage = {}
        for week in range(1, len(self.weeks)):
            prev_inventory = results['inventory_levels'][week-1]
            consumption = results['consumption_schedule'][week]
            for item in self.items:
                if self.food_items[item]['perishable']:
                    prev_qty = prev_inventory.get(item, 0)
                    consumed = consumption.get(item, 0)
                    if prev_qty > consumed:
                        total_wastage[item] = total_wastage.get(item, 0) + (prev_qty - consumed)
        
        # Add summary rows
        total_cost = results['cost_breakdown']['total']
        wastage_cost = sum(total_wastage.get(item, 0) * self.food_items[item]['cost'] 
                          for item in total_wastage)
        
        summary_rows = [
            {
                'Week': 'TOTAL WASTAGE',
                'Orders': '',
                'Consumption Plan': '',
                'Remaining Inventory': '',
                'Wastage': '\n'.join(f"{item}: {qty} servings (${qty * self.food_items[item]['cost']:.2f})"
                                   for item, qty in total_wastage.items()) if total_wastage else "None",
                'Total Cost': f"${wastage_cost:.2f} wasted"
            },
            {
                'Week': 'TOTAL COST',
                'Orders': '',
                'Consumption Plan': '',
                'Remaining Inventory': '',
                'Wastage': '',
                'Total Cost': f"${total_cost:.2f}"
            }
        ]
        
        df = pd.concat([df, pd.DataFrame(summary_rows)], ignore_index=True)
        
        return df
    
    def _format_weekly_action_plan(self, results, date_strs):
        """Format a simplified weekly action plan showing orders, consumption, and wastage."""
        rows = []
        
        for week, date in enumerate(date_strs):
            orders = results['order_schedule'][week]
            consumption = results['consumption_schedule'][week]
            inventory = results['inventory_levels'][week]
            
            # Calculate wastage for perishable items
            wastage = {}
            if week > 0:  # Can only calculate wastage from second week onwards
                prev_inventory = results['inventory_levels'][week-1]
                for item in self.items:
                    if self.food_items[item]['perishable']:
                        # Wastage = previous inventory - consumption
                        prev_qty = prev_inventory.get(item, 0)
                        consumed = consumption.get(item, 0)
                        if prev_qty > consumed:
                            wastage[item] = prev_qty - consumed
            
            # Only include items that need to be ordered, consumed, or have wastage this week
            active_items = set()
            for item in self.items:
                if (item in orders and orders[item]['servings'] > 0) or \
                   (item in consumption and consumption[item] > 0) or \
                   (item in wastage and wastage[item] > 0):
                    active_items.add(item)
            
            if active_items:  # Only add weeks where there's activity
                order_text = []
                consume_text = []
                inventory_text = []
                wastage_text = []
                
                for item in sorted(active_items):
                    # Add order information if there's an order this week
                    if item in orders and orders[item]['servings'] > 0:
                        pkg_text = f"({orders[item]['packages']} packages)" if orders[item]['packages'] > 1 else "(1 package)"
                        order_text.append(f"{item}: {orders[item]['servings']} servings {pkg_text}")
                    
                    # Add consumption information
                    if item in consumption and consumption[item] > 0:
                        consume_text.append(f"{item}: {consumption[item]} servings")
                    
                    # Add inventory information
                    if item in inventory and inventory[item] > 0:
                        inventory_text.append(f"{item}: {inventory[item]} servings")
                    
                    # Add wastage information
                    if item in wastage and wastage[item] > 0:
                        wastage_text.append(f"{item}: {wastage[item]} servings")
                
                row = {
                    'Week': date,
                    'Orders': '\n'.join(order_text) if order_text else "No orders needed",
                    'Consumption Plan': '\n'.join(consume_text),
                    'Remaining Inventory': '\n'.join(inventory_text) if inventory_text else "None",
                    'Wastage': '\n'.join(wastage_text) if wastage_text else "None",
                    'Total Cost': f"${results['cost_breakdown']['weekly'][week]['total']:.2f}"
                }
                rows.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(rows)
        
        # Calculate total wastage
        total_wastage = {}
        for week in range(1, len(self.weeks)):
            prev_inventory = results['inventory_levels'][week-1]
            consumption = results['consumption_schedule'][week]
            for item in self.items:
                if self.food_items[item]['perishable']:
                    prev_qty = prev_inventory.get(item, 0)
                    consumed = consumption.get(item, 0)
                    if prev_qty > consumed:
                        total_wastage[item] = total_wastage.get(item, 0) + (prev_qty - consumed)
        
        # Add summary rows
        total_cost = results['cost_breakdown']['total']
        wastage_cost = sum(total_wastage.get(item, 0) * self.food_items[item]['cost'] 
                          for item in total_wastage)
        
        summary_rows = [
            {
                'Week': 'TOTAL WASTAGE',
                'Orders': '',
                'Consumption Plan': '',
                'Remaining Inventory': '',
                'Wastage': '\n'.join(f"{item}: {qty} servings (${qty * self.food_items[item]['cost']:.2f})"
                                   for item, qty in total_wastage.items()) if total_wastage else "None",
                'Total Cost': f"${wastage_cost:.2f} wasted"
            },
            {
                'Week': 'TOTAL COST',
                'Orders': '',
                'Consumption Plan': '',
                'Remaining Inventory': '',
                'Wastage': '',
                'Total Cost': f"${total_cost:.2f}"
            }
        ]
        
        df = pd.concat([df, pd.DataFrame(summary_rows)], ignore_index=True)
        
        return df
    
    def print_results(self):
        """Print formatted results to console."""
        results = self.get_formatted_results()
        if not results:
            print("No results to display - optimization failed.")
            return
        
        # Get the weekly action plan
        date_strs = [col for col in results['weekly_schedule']['Week'].unique() if col != 'TOTAL']
        action_plan = self._format_weekly_action_plan(self.get_results(), date_strs)
        
        print("\n=== WEEKLY ACTION PLAN ===")
        print("What to order and eat each week:\n")
        pd.set_option('display.max_colwidth', None)
        pd.set_option('display.max_rows', None)
        print(action_plan.to_string(index=False))
        
        print("\nDetailed breakdowns:")
        print("\n=== COST SUMMARY ===")
        print(results['cost_summary'].to_string(index=False))
        
        print("\n=== NUTRITIONAL SUMMARY ===")
        print(results['nutritional_summary'].to_string(index=False))
        
        # Save results to CSV files
        output_dir = 'output'
        os.makedirs(output_dir, exist_ok=True)
        
        action_plan.to_csv(f'{output_dir}/weekly_action_plan.csv', index=False)
        results['cost_summary'].to_csv(f'{output_dir}/cost_summary.csv', index=False)
        results['nutritional_summary'].to_csv(f'{output_dir}/nutritional_summary.csv', index=False)
        
        print(f"\nDetailed results have been saved to the '{output_dir}' directory.")

if __name__ == "__main__":
    optimizer = DietOptimizer()
    optimizer.print_results() 