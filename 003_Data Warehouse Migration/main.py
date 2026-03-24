# Day 3: The Data Warehouse Migration Challenge
# Concept: Nested Conditionals (If/Elif/Else)

print("""
*******************************************************************************  
         |    SERVER ROOM: DATA WAREHOUSE MIGRATION           |
*******************************************************************************
""")
print("Welcome to the Migration Challenge.")
print("Your mission is to move the legacy API data into BigQuery without data loss.")

# First Decision: Architecture Choice
choice1 = input('You are at the ingestion layer. Do you go "left" toward the Python pipeline or "right" toward the legacy manual upload? ').lower()

if choice1 == "left":
    # Second Decision: Processing Strategy
    choice2 = input('You reached the processing lake. Do you "wait" for the automated validation script to run, or "swim" and push the raw data immediately? ').lower()
    if choice2 == "wait":
        print("The script finished. Data is clean.")
        choice3 = input("You stand before three storage doors: 'Red' (Unpartitioned), 'Blue' (Clustered), or 'Yellow' (Partitioned & Clustered). Which do you choose? ").lower()
        
        if choice3 == "yellow":
            print("\nSUCCESS! You optimized the storage perfectly.")
            print("The dashboard loads in < 2 seconds. Your manager is impressed.")
            print("YOU WIN THE PROMOTION!")
        elif choice3 == "red":
            print("\nFAILURE. The table is too large and the query timed out.")
            print("The client is angry about the slow dashboard. Game Over.")
        elif choice3 == "blue":
            print("\nFAILURE. You clustered but didn't partition. The bytes scanned are too high.")
            print("You blew the BigQuery budget. Game Over.")
        else:
            print("\nERROR. Invalid configuration. The pipeline crashed. Game Over.")
            
    else:
        print("\nCRITICAL FAILURE. You pushed raw data with duplicates.")
        print("The BI platform crashed due to data grain issues. Game Over.")

else:
    print("\nFAILURE. Manual uploads are not 'Parameterized' or 'Composable'.")
    print("Your manager caught you copy-pasting code. Game Over.")