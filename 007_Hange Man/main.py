import random

# --- 1. GLOBAL DATA ---
word_list = [
    "python", "hangman", "developer", "function", "variable",
    "loop", "condition", "string", "list", "module", "class"
]

# ASCII stages ordered from 0 lives (dead) to 5+ lives (empty)
stages = [
    """
       +---+
       |   |
       O   |
      /|\\  |
      / \\  |
           |
    =========""", # 0 lives: Dead
    """
       +---+
       |   |
       O   |
      /|\\  |
      /    |
           |
    =========""", # 1 life
    """
       +---+
       |   |
       O   |
      /|\\  |
           |
           |
    =========""", # 2 lives
    """
       +---+
       |   |
       O   |
      /|   |
           |
           |
    =========""", # 3 lives
    """
       +---+
       |   |
       O   |
           |
           |
           |
    =========""", # 4 lives
    """
       +---+
       |   |
           |
           |
           |
           |
    ========="""  # 5+ lives: Clear
]

# --- 2. FUNCTIONS ---

def choose_difficulty():
    """Sets starting lives based on user choice."""
    print("\nSelect Difficulty Level:")
    print("1. Easy (8 lives)\n2. Medium (6 lives)\n3. Hard (4 lives)")
    choice = input("Enter 1, 2, or 3: ").strip()
    if choice == "1":
        return 8
    elif choice == "3":
        return 4
    else:
        return 6

def display_status(display, lives, guessed_letters):
    """Prints the current word progress, lives, and ASCII art."""
    print("\n" + " ".join(display))
    print(f"Lives remaining: {lives}")
    print(f"Letters tried: {', '.join(sorted(guessed_letters))}")
    
    # Map lives to the correct stage index
    if lives < len(stages):
        print(stages[lives])
    else:
        print(stages[-1])

def get_hint(word, display):
    """Finds a letter in the word that hasn't been revealed yet."""
    potential_hints = []
    for letter in word:
        if letter not in display:
            potential_hints.append(letter)
    
    if len(potential_hints) > 0:
        return random.choice(potential_hints)
    return None

def play_game():
    """Contains the primary loop for one round of Hangman."""
    print("\n Welcome to HANGMAN ADVANCED!")
    player_name = input("Enter your name: ").strip().upper()
    
    lives = choose_difficulty()
    chosen_word = random.choice(word_list)
    
    # Create the underscores for the word
    display = []
    for _ in range(len(chosen_word)):
        display.append("_")
        
    guessed_letters = []
    hint_used = False
    score = 0

    # MAIN GAME LOOP
    while "_" in display and lives > 0:
        display_status(display, lives, guessed_letters)
        
        user_input = input("\nGuess a letter, type 'hint', or guess the WHOLE word: ").lower().strip()

        # LOGIC FIX: Handle Full Word Guesses
        if len(user_input) > 1 and user_input != "hint":
            if user_input == chosen_word:
                for i in range(len(chosen_word)):
                    display[i] = chosen_word[i]
                print(f" BRILLIANT! You guessed the entire word: {chosen_word.upper()}!")
                break
            else:
                print(f" '{user_input}' is not the secret word! You lose 2 lives.")
                lives -= 2
                continue

        # Handle Hint
        if user_input == "hint":
            if not hint_used:
                hint_letter = get_hint(chosen_word, display)
                if hint_letter:
                    print(f" HINT: The word contains the letter '{hint_letter}'.")
                    hint_used = True
                    score -= 5
                else:
                    print("No hints available for this word!")
            else:
                print("You already used your hint for this round.")
            continue

        # Single Letter Validation
        if not user_input.isalpha() or len(user_input) == 0:
            print("Please enter a valid letter (A-Z).")
            continue

        if user_input in guessed_letters:
            print(f"You already guessed '{user_input}'. Try another one.")
            continue

        # Process the guess
        guessed_letters.append(user_input)

        if user_input in chosen_word:
            print(f"Yes! '{user_input}' is in the word.")
            # Update all matching positions
            for i in range(len(chosen_word)):
                if chosen_word[i] == user_input:
                    display[i] = user_input
            score += 10
        else:
            print(f" No, '{user_input}' is not there.")
            lives -= 1
            score -= 5

    # --- 3. END OF ROUND RESULTS ---
    if "_" not in display:
        final_score = score + (max(0, lives) * 10)
        print(f"\nWELL DONE {player_name}!")
        print(f"The word was indeed: {chosen_word.upper()}")
        print(f"Final Score: {final_score}")
    else:
        print(f"\nGAME OVER, {player_name}.")
        print(stages[0]) 
        print(f"The word you missed was: {chosen_word.upper()}")
        print(f"Final Score: {score}")

# --- 4. PROGRAM START ---

if __name__ == "__main__":
    is_running = True
    while is_running:
        play_game()
        choice = input("\nPlay another round? (y/n): ").lower().strip()
        if choice != "y":
            is_running = False
            print("\nThanks for playing Python Hangman. See you next time!")