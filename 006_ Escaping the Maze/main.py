# Day 6: Escaping the Maze
# Concepts: Functions, While Loops, If/Elif/Else, Lists, and Randomization.

import random

# --- 1. SETUP THE GAME ASSETS (Day 1, 2, 4) ---
print("***************************************")
print("Welcome to the Python Maze Escape!")
print("Your goal is to reach the treasure (X)")
print("***************************************")

# Using a list to represent the "world" status
# True means the path is clear, False means there is a wall
path_options = [True, True, True, False] 

# --- 2. DEFINE THE FUNCTIONS (Day 6) ---
def turn_left():
    print("Turning Left... ⟲")

def move_forward():
    print("Moving Forward... ↑")

def is_front_blocked():
    # Randomly decides if the front is blocked based on our list
    return not random.choice(path_options)

def wall_on_right():
    # Randomly decides if there is a wall on the right
    return random.choice([True, False])

# --- 3. THE MAZE LOGIC (Day 6 While Loops & Conditionals) ---

# We define our goal status
at_goal = False
steps_taken = 0

# A while loop continues until we reach the goal
while not at_goal:
    steps_taken += 1
    print(f"\n--- Step {steps_taken} ---")

    # Day 6: Calling functions and using nested Indentation
    if is_front_blocked():
        print("Front is blocked!")
        if wall_on_right():
            print("Wall on right. Must turn left.")
            turn_left()
        else:
            print("No wall on right, but front is blocked. Turning left.")
            turn_left()
    else:
        move_forward()

    # Manual "Goal" trigger for the script (Day 3/5 Logic)
    # Let's say the maze is 10 successful steps long
    if steps_taken == 10:
        at_goal = True

# --- 4. FINAL OUTPUT (Day 1-2) ---
print("\n***************************************")
print("CONGRATULATIONS!")
print(f"You escaped the maze in {steps_taken} steps.")
print("The treasure is yours!")
print("***************************************")