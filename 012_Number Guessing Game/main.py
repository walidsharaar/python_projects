# Day 12: Advanced Number Guessing Game
# Learning Goals: Global vs. Local Scope, Constants, and Functional Logic.
# Manager Alignment: "Write maintainable code with clear variable namespaces."

import random

# --- GLOBAL CONSTANTS ---
# Use uppercase for constants. These are fixed values that don't change 
# during execution, making the code "Parameterized."
EASY_LEVEL_TURNS = 10
HARD_LEVEL_TURNS = 5

def check_answer(guess, answer, turns):
    """
    Checks the user's guess against the answer. 
    Returns the remaining number of turns (Functional Output).
    """
    if guess > answer:
        print("Too high. ")
        return turns - 1
    elif guess < answer:
        print("Too low. ")
        return turns - 1
    else:
        print(f" You got it! The answer was {answer}.")
        return 0 # Setting turns to 0 to end the loop

def set_difficulty():
    """Sets the initial 'State' based on user choice."""
    level = input("Choose a difficulty. Type 'easy' or 'hard': ").lower()
    if level == "hard":
        return HARD_LEVEL_TURNS
    else:
        return EASY_LEVEL_TURNS

def game():
    """Main Game Engine."""
    print("\n" + "="*40)
    print("Welcome to the Number Guessing Game!")
    print("I'm thinking of a number between 1 and 100.")
    print("="*40)

    # Local Variables (Scoped only to this function)
    answer = random.randint(1, 100)
    turns = set_difficulty()
    
    # Debugging line for development (comment out for production)
    # print(f"Psst, the secret number is {answer}")

    guess = 0
    while guess != answer:
        print(f"You have {turns} attempts remaining to guess the number.")
        
        # User input with basic type validation
        try:
            guess = int(input("Make a guess: "))
        except ValueError:
            print("Invalid input. Please enter a number.")
            continue

        # Track turns using the function return (Avoiding the 'global' keyword)
        turns = check_answer(guess, answer, turns)

        if turns == 0 and guess != answer:
            print(f"\n You've run out of guesses. Game Over. The number was {answer}.")
            return # Exit the function
        elif guess != answer:
            print("Guess again.")

# Entry Point
if __name__ == "__main__":
    game()
