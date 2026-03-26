# Day 10: Professional Calculator (Functions with Outputs)
# Learning Goals: Multiple Return Values, Docstrings, and Recursion.
# Manager Alignment: "Write modular, documented code that is reusable across the stack."

def add(n1, n2):
    """Adds two numbers together."""
    return n1 + n2

def subtract(n1, n2):
    """Subtracts n2 from n1."""
    return n1 - n2

def multiply(n1, n2):
    """Multiplies two numbers."""
    return n1 * n2

def divide(n1, n2):
    """Divides n1 by n2. Includes basic zero-division safety."""
    if n2 == 0:
        return "Error: Division by zero"
    return n1 / n2

# Dictionary mapping symbols to our transformation functions
operations = {
    "+": add,
    "-": subtract,
    "*": multiply,
    "/": divide
}

def calculator():
    """
    The main calculator engine. 
    Uses recursion to restart the program while maintaining clean memory.
    """
    print("\n--- Python Data Calculator [v1.0] ---")
    
    num1 = float(input("What's the first number?: "))
    
    # Show available transformation symbols
    for symbol in operations:
        print(symbol)

    should_continue = True
    
    while should_continue:
        operation_symbol = input("Pick an operation: ")
        num2 = float(input("What's the next number?: "))
        
        # Select the function from our dictionary (Functional Programming)
        calculation_function = operations[operation_symbol]
        answer = calculation_function(num1, num2)

        print(f"{num1} {operation_symbol} {num2} = {answer}")

        choice = input(f"Type 'y' to continue calculating with {answer}, 'n' to start fresh, or 'e' to exit: ").lower()
        
        if choice == 'y':
            num1 = answer
        elif choice == 'n':
            should_continue = False
            clear_screen()
            calculator() # RECURSION: Function calls itself to restart
        else:
            should_continue = False
            print("Calculation session terminated.")

def clear_screen():
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

# Start the program
if __name__ == "__main__":
    calculator()

