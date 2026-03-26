# Day 09: Secret Auction (Dictionaries & Nesting)
# Learning Goal: Using Dictionaries to store and compare relational data.

# To clear the console for privacy between bidders
import os

def clear():
    """Clears the console screen across different operating systems."""
    # For Windows: 'cls', for Mac/Linux: 'clear'
    os.system('cls' if os.name == 'nt' else 'clear')

logo = '''
                         ___________
                         \         /
                          )_______(
                          |"""""""|_.-._,.---------.,_.-._
                          |       | | |               | | ''-.
                          |       |_| |_             _| |_..-'
                          |_______| '-' `'---------'` '-'
                          )"""""""(
                         /_________\\
                       .-------------.
                      /_______________\\
'''

def find_highest_bidder(bidding_record):
    """
    Iterates through the dictionary to find the highest value (bid)
    and identifies the corresponding key (name).
    """
    highest_bid = 0
    winner = ""
    
    # bidding_record = {"Name": Price, "Name2": Price2}
    for bidder in bidding_record:
        bid_amount = bidding_record[bidder]
        if bid_amount > highest_bid:
            highest_bid = bid_amount
            winner = bidder
            
    print(f"The winner is {winner} with a bid of ${highest_bid:,.2f}")

# --- Main Program Logic ---

print(logo)
print("Welcome to the Secret Auction program.")

# Dictionary to store Name (Key) and Bid (Value)
bids = {}
bidding_finished = False

while not bidding_finished:
    name = input("What is your name?: ")
    price = int(input("What is your bid?: $"))
    
    # Add to dictionary
    bids[name] = price
    
    should_continue = input("Are there any other bidders? Type 'yes' or 'no'.\n").lower()
    
    if should_continue == "no":
        bidding_finished = True
        clear()
        find_highest_bidder(bids)
    elif should_continue == "yes":
        clear()
    else:
        print("Invalid input. Ending auction and calculating result.")
        bidding_finished = True
        find_highest_bidder(bids)