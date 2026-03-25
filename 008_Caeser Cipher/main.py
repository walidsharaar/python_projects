1. DEFINE a list containing all letters of the alphabet (a-z).
2. DEFINE a function 'caesar' that takes three parameters:
   - input_text (the message)
   - shift_amount (the number to shift by)
   - cipher_direction (whether to 'encode' or 'decode')
3. INSIDE the function:
   - CREATE an empty string for the result.
   - IF the direction is 'decode', make the shift_amount negative.
   - LOOP through each character in the input_text:
     - IF the character is in the alphabet:
       - FIND its current index.
       - CALCULATE the new index (current index + shift_amount).
       - USE the Modulo operator (%) to wrap around the alphabet (z back to a).
       - ADD the new letter to the result string.
     - ELSE (if it's a space or number):
       - ADD the original character to the result without changing it.
   - PRINT the final encrypted or decrypted message.
4. START a while loop to keep the program running:
   - GET user inputs for direction, message, and shift.
   - CALL the 'caesar' function with those inputs.
   - ASK if they want to go again.