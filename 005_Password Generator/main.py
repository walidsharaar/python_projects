# Day 5: Professional Password Generator
# Concepts: For Loops, Range(), Lists, and Randomization.


import random

#  Character Lists (Data Sources)
letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
symbols = ['!', '#', '$', '%', '&', '(', ')', '*', '+']

print("--- System Credential Generator ---")

# Step 1: Capture Parameters (Business Requirements)
nr_letters = int(input("How many letters should the credential have?\n")) 
nr_symbols = int(input("How many symbols should it include?\n"))
nr_numbers = int(input("How many numbers are required for compliance?\n"))

# Step 2: Initialize an empty list to store the 'Batch' of characters
# Using a list instead of a string allows for easy shuffling later
password_list = []

# Step 3: Use For Loops with the Range() function to populate the list
# This simulates 'Batch Processing' logic.
for char in range(0, nr_letters):
    password_list.append(random.choice(letters))

for char in range(0, nr_symbols):
    password_list.append(random.choice(symbols))

for char in range(0, nr_numbers):
    password_list.append(random.choice(numbers))

# Step 4: Randomization (Shuffling the batch)
random.shuffle(password_list)

# Step 5: Final String Assembly
password = ""
for char in password_list:
    password += char

# Output Results 
print("\n" + "="*45)
print(f"GENERATED CREDENTIAL: {password}")
print("="*45)
