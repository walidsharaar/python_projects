
"""
Day 2 Project: Tip Calculator
This project will use EVERY concept I learned today. 

The Problem:
I'm at a restaurant. I want to:
Calculate the tip based on percentage
Split the bill among multiple people
Show the final amount each person pays
"""

"""
Requirements:
My program should:
Ask for the total bill amount
Ask for the tip percentage (10%, 12%, 15%, or custom)
Ask how many people are splitting the bill
Calculate: (bill + tip) / people
Display the final amount per person (rounded to 2 decimals)
"""

#  (Step 1)

print("Welcome to the Tip Calculator!")

# Get bill amount
bill = input("What was the total bill? $")

# Print it back to verify
print(f"Bill amount: ${bill}")
print(f"Type of bill: {type(bill)}") 

#  (Step 2)

print("Welcome to the Tip Calculator!")

# Get and convert bill amount
bill = float(input("What was the total bill? $"))

# Get tip percentage
tip_percent = float(input("What percentage tip would you like to give? (10, 12, 15) "))

# Calculate
tip_amount = bill * (tip_percent / 100)
total = bill + tip_amount

# Display results
print(f"Tip amount: ${tip_amount}")
print(f"Total including tip: ${total}")

#  (Step 3)

print("Welcome to the Tip Calculator!")

# Get inputs
bill = float(input("What was the total bill? $"))
tip_percent = float(input("What percentage tip would you like to give? (10, 12, 15) "))
people = int(input("How many people are splitting the bill? "))

# Calculate
tip_amount = bill * (tip_percent / 100)
total = bill + tip_amount
per_person = total / people

# Display results
print(f"Total bill with tip: ${total}")
print(f"Each person pays: ${per_person}")

#  (Step 4)

print("Welcome to the Tip Calculator!")
