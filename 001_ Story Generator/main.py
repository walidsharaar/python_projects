# story_generator.py

print("Welcome to the Story Generator!")
print("=" * 40)

# Get user inputs
name = input("Enter a name: ")
adjective = input("Enter an adjective: ")
noun = input("Enter a noun: ")
verb = input("Enter a verb ending in -ing: ")
place = input("Enter a place: ")

# Create the story
# You'll write the story here using your variables
# Print the story
print("\nHere's your story:")
print("=" * 40)    
# Print the story with formatting
print(f"Once upon a time, {name} went to {place}. ")
print(f"They saw a {adjective} {noun} that was {verb}!")
print(f"{name} couldn't believe their eyes. ")
print(f'"This is the most {adjective} day ever!" they shouted.')
