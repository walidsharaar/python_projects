# Day 4: Rock, Paper, Scissors (Data-Driven Refactor)
# Concepts: Randomization, Python Lists, and Nested List Indexing.

import random

# ASCII Art for professional-looking output
rock = '''
    _______
---'   ____)
      (_____)
      (_____)
      (____)
---.__(___)
'''

paper = '''
    _______
---'   ____)____
          ______)
          _______)
         _______)
---.__________)
'''

scissors = '''
    _______
---'   ____)____
          ______)
       __________)
      (____)
---.__(___)
'''

# Day 4 Concept: The List
game_images = [rock, paper, scissors]
CHOICES = ["rock", "paper", "scissors"]


# Day 4 Concept: The Nested List (The Win/Loss Matrix)
# Index mapping: 0 = Rock, 1 = Paper, 2 = Scissors
# Matrix values: 0 = Draw, 1 = User Wins, 2 = Computer Wins
# This matrix replaces the messy "if user == rock and computer == scissors" logic.
LOGIC_MATRIX = [
    [0, 2, 1], # User chose Rock vs [Rock, Paper, Scissors]
    [1, 0, 2], # User chose Paper vs [Rock, Paper, Scissors]
    [2, 1, 0]  # User chose Scissors vs [Rock, Paper, Scissors]
]

print("--- Rock, Paper, Scissors ---")


# Capture User Input
user_input = input("What do you choose? Type 0 for Rock, 1 for Paper, 2 for Scissors.\n")

# Basic QA check to prevent IndexErrors
if not user_input.isdigit():
    print("Critical Error: Selection must be a number.")
else:
    user_idx = int(user_input)
    
    if user_idx >= 3 or user_idx < 0:
        print("Out Of Bounds: Selection must be 0, 1, or 2.")
    else:
        # Display User choice
        print(f"\nYou chose {CHOICES[user_idx]}:")
        print(game_images[user_idx])

        # Randomize Computer choice
        computer_idx = random.randint(0, 2)
        print(f"Computer chose {CHOICES[computer_idx]}:")
        print(game_images[computer_idx])

        result = LOGIC_MATRIX[user_idx][computer_idx]

        if result == 0:
            print("Outcome: It's a draw.")
        elif result == 1:
            print("Outcome: You win!")
        else:
            print("Outcome: You lose.")