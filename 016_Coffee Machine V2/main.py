# Day 16: Coffee Machine (Object-Oriented Programming)
# Learning Goals: Classes, Objects, Attributes, and Methods.

# MenuItem Class: Models each drink on the menu with its ingredients and cost.

        self.name = name
        self.cost = cost
        self.ingredients = {
            "water": water,
            "milk": milk,
            "coffee": coffee
        }

# Menu Class: Models the Menu with drinks.

        """Searches the menu for a particular drink by name. Returns that item if it exists, otherwise returns None."""
        for item in self.menu:
            if item.name == order_name:
                return item
        print("Sorry that item is not available.")
        return None
# CoffeeMaker Class: Models the machine that makes the coffee.

# MoneyMachine Class: Models the payment processing system.

# --- MAIN EXECUTION (The Orchestrator) ---
