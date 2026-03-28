# Day 14: Higher Lower Game (The Capstone of Foundations)
# Learning Goals: Data extraction, formatting, and game state management.


import random
import os

# --- DATA SOURCE ---
# In a real engineering role, this would be an API or a SQL Table.
data = [
    {'name': 'Instagram', 'follower_count': 648, 'description': 'Social media platform', 'country': 'United States'},
    {'name': 'Cristiano Ronaldo', 'follower_count': 600, 'description': 'Footballer', 'country': 'Portugal'},
    {'name': 'Lionel Messi', 'follower_count': 482, 'description': 'Footballer', 'country': 'Argentina'},
    {'name': 'Selena Gomez', 'follower_count': 429, 'description': 'Musician and actress', 'country': 'United States'},
    {'name': 'Kylie Jenner', 'follower_count': 400, 'description': 'Reality TV personality and businesswoman', 'country': 'United States'},
    {'name': 'Dwayne Johnson', 'follower_count': 391, 'description': 'Actor and professional wrestler', 'country': 'United States'},
    {'name': 'Ariana Grande', 'follower_count': 380, 'description': 'Musician and actress', 'country': 'United States'},
    {'name': 'Kim Kardashian', 'follower_count': 364, 'description': 'Reality TV personality and businesswoman', 'country': 'United States'},
    {'name': 'Beyoncé', 'follower_count': 315, 'description': 'Musician', 'country': 'United States'},
    {'name': 'Justin Bieber', 'follower_count': 293, 'description': 'Musician', 'country': 'Canada'}
]

logo = """
    __  ___       __             
   / / / (_)___ _/ /_  ___  _____
  / /_/ / / __ `/ __ \/ _ \/ ___/
 / __  / / /_/ / / / /  __/ /    
/_/ ///_/\__, /_/ /_/\___/_/     
   / /  /____/_      _____  _____
  / /   / __ \ | /| / / _ \/ ___/
 / /___/ /_/ / |/ |/ /  __/ /    
/_____/\____/|__/|__/\___/_/     
"""

vs = """
 _    __    
| |  / /____
| | / / ___/
| |/ (__  ) 
|___/____(_)
"""

def clear():
    """Clears the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def format_data(account):
    """Takes the account data and returns a printable format."""
    name = account["name"]
    description = account["description"]
    country = account["country"]
    return f"{name}, a {description}, from {country}"

def check_answer(guess, a_followers, b_followers):
    """Checks if the user's guess is correct based on follower counts."""
    if a_followers > b_followers:
        return guess == "a"
    else:
        return guess == "b"

def game():
    print(logo)
    score = 0
    game_should_continue = True
    
    # Generate initial accounts
    account_a = random.choice(data)
    account_b = random.choice(data)

    while game_should_continue:
        # Step 1: Ensure account_a and account_b are not the same
        while account_a == account_b:
            account_b = random.choice(data)

        print(f"Compare A: {format_data(account_a)}.")
        print(vs)
        print(f"Against B: {format_data(account_b)}.")

        # Step 2: Get user guess
        guess = input("Who has more followers? Type 'A' or 'B': ").lower()

        # Step 3: Extract follower counts
        a_follower_count = account_a["follower_count"]
        b_follower_count = account_b["follower_count"]

        # Step 4: Validate answer
        is_correct = check_answer(guess, a_follower_count, b_follower_count)

        clear()
        print(logo)

        if is_correct:
            score += 1
            print(f"You're right! Current score: {score}.")
            # Move B to A so the game chains forward
            account_a = account_b
            account_b = random.choice(data)
        else:
            game_should_continue = False
            print(f"Sorry, that's wrong. Final score: {score}")

# --- EXECUTION ---
if __name__ == "__main__":
    game()

