# Day 3: The Data Warehouse Migration Challenge
# Concept: Nested Conditionals (If/Elif/Else)
DISPLAY Welcome Banner and Mission Instructions

PROMPT user for choice1: "left" or "right"
CONVERT choice1 to lowercase

IF choice1 is "left":
    PROMPT user for choice2: "wait" or "swim"
    CONVERT choice2 to lowercase
    
    IF choice2 is "wait":
        DISPLAY "Data is clean."
        PROMPT user for choice3: "red", "blue", or "yellow"
        CONVERT choice3 to lowercase
        
        IF choice3 is "yellow":
            DISPLAY "SUCCESS! Optimized storage. YOU WIN!"
        ELSE IF choice3 is "red":
            DISPLAY "FAILURE. Query timed out."
        ELSE IF choice3 is "blue":
            DISPLAY "FAILURE. Over budget."
        ELSE:
            DISPLAY "ERROR. Pipeline crashed."
            
    ELSE:
        DISPLAY "CRITICAL FAILURE. Duplicate data detected."

ELSE:
    DISPLAY "FAILURE. Manual uploads are not scalable."