# Day 8: Caesar Cipher (Function Parameters & Reuse)
# Learning Goal: Moving from static functions to parameterized tools.

alphabet = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

def caesar(start_text, shift_amount, cipher_direction):
    """
    Encrypts or Decrypts text based on the shift and direction provided.
    """
    end_text = ""
    
    # If decoding, we shift backwards
    if cipher_direction == "decode":
        shift_amount *= -1
        
    for char in start_text:
        if char in alphabet:
            # Find current position
            position = alphabet.index(char)
            
            # Calculate new position using Modulo 26
            # This handles 'wrap-around' (z -> a) and very large shift numbers
            new_position = (position + shift_amount) % 26
            
            end_text += alphabet[new_position]
        else:
            # Keep numbers, symbols, and spaces as they are
            end_text += char
            
    print(f"The {cipher_direction}d result is: {end_text}")

# --- User Interface ---

logo = """           
 ,adPPYba, ,adPPYYba,  ,adPPYba, ,adPPYba, ,adPPYYba, 8b,dPPYba,  
a8"     "" ""     `Y8 a8P_____88 I8[    "" ""     `Y8 88P'   "Y8  
8b         ,adPPPPP88 8PP\"\"\"\"\"\"\"  `"Y8ba,  ,adPPPPP88 88          
"8a,   ,aa 88,    ,88 "8b,   ,aa aa    ]8I 88,    ,88 88          
 `"Ybbd8"' `"8bbdP"Y8  `"Ybbd8"' `"YbbdP"' `"8bbdP"Y8 88   
            88             88                                 
           ""             88                                 
                          88                                 
 ,adPPYba, 88 8b,dPPYba,  88,dPPYba,   ,adPPYba, 8b,dPPYba,  
a8"     "" 88 88P'    "8a 88P'    "8a a8P_____88 88P'   "Y8  
8b         88 88       d8 88       88 8PP\"\"\"\"\"\"\" 88          
"8a,   ,aa 88 88b,   ,a8" 88       88 "8b,   ,aa 88          
 `"Ybbd8"' 88 88`YbbdP"'  88       88  `"Ybbd8"' 88          
              88                                             
              88           
"""

print(logo)

should_continue = True
while should_continue:
    direction = input("Type 'encode' to encrypt, type 'decode' to decrypt:\n").lower()
    text = input("Type your message:\n").lower()
    shift = int(input("Type the shift number:\n"))

    # Calling the function using Keyword Arguments for clarity
    caesar(start_text=text, shift_amount=shift, cipher_direction=direction)

    restart = input("\nType 'yes' if you want to go again. Otherwise type 'no'.\n").lower()
    if restart == "no":
        should_continue = False
        print("Goodbye! Communications secured.")