# Day 24: Interactive Mail Merge Automation 
# Learning Goals: Interactive CLI, Pathlib, Logging, and Multi-Variable Hydration.


import logging
from pathlib import Path

# --- CONFIGURATION ---
BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "Input"
NAMES_FILE = INPUT_DIR / "Names" / "invited_names.txt"
LETTER_TEMPLATE = INPUT_DIR / "Letters" / "starting_letter.txt"
OUTPUT_DIR = BASE_DIR / "Output" / "ReadyToSend"

# Placeholders for dynamic replacement - Consistency is key
BIRTHDAY_PERSON_PLACEHOLDER = "[BirthdayPerson]"
NAME_PLACEHOLDER = "[Name]"
DATE_PLACEHOLDER = "[Date]"
VENUE_PLACEHOLDER = "[Venue]"

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def setup_environment():
    """Ensures input and output directories exist and are ready."""
    INPUT_DIR.joinpath("Names").mkdir(parents=True, exist_ok=True)
    INPUT_DIR.joinpath("Letters").mkdir(parents=True, exist_ok=True)
    
    if OUTPUT_DIR.exists():
        for file in OUTPUT_DIR.glob("*.txt"):
            file.unlink()
    else:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logging.info("Environment and directories initialized.")

def collect_user_input():
    """Interactively collects event details and guest names from the user."""
    print("\n--- STEP 1: PARTY DETAILS ---")
    birthday_person = input("Whose birthday is it? ").strip()
    bday_date = input(f"Enter {birthday_person}'s birthday date (e.g. Oct 31st): ").strip()
    venue_name = input("Enter the Venue (e.g. The Sky Lounge): ").strip()

    print("\n--- STEP 2: COLLECT GUEST LIST ---")
    print("Enter guest names (type 'done' when finished):")
    
    names_list = []
    while True:
        name = input("> ").strip()
        if name.lower() == 'done':
            break
        if name:
            names_list.append(name)
    
    # Save guest list for audit
    with open(NAMES_FILE, mode="w", encoding="utf-8") as file:
        file.write("\n".join(names_list))
    
    # Define the final hardcoded message structure
    message_template = (
        f"Squad! {BIRTHDAY_PERSON_PLACEHOLDER}’s birthday is {DATE_PLACEHOLDER} 🎉\n\n"
        f"Hey {NAME_PLACEHOLDER}, you're invited to celebrate at {VENUE_PLACEHOLDER}.\n"
        f"Let’s make it epic! 🎂"
    )
    
    # Store the template for reference
    with open(LETTER_TEMPLATE, mode="w", encoding="utf-8") as file:
        file.write(message_template)
        
    return names_list, message_template, birthday_person, bday_date, venue_name

def perform_mail_merge():
    """Main execution logic for unique per-person hydration."""
    setup_environment()
    
    # Capture data from the user
    names, template, bday_person, date, venue = collect_user_input()
    
    if not names:
        logging.warning("No guests provided. Automation aborted.")
        return

    print("\n--- STEP 3: GENERATING SQUAD INVITES ---")
    
    count = 0
    for name in names:
        # Chain replacements for all variables
        content = template.replace(BIRTHDAY_PERSON_PLACEHOLDER, bday_person)
        content = content.replace(DATE_PLACEHOLDER, date)
        content = content.replace(VENUE_PLACEHOLDER, venue)
        content = content.replace(NAME_PLACEHOLDER, name)
        
        # Sanitize filename
        safe_name = name.replace(" ", "_")
        file_path = OUTPUT_DIR / f"invite_{safe_name}.txt"
        
        try:
            with open(file_path, mode="w", encoding="utf-8") as output_file:
                output_file.write(content)
            count += 1
            print(f"Generated: {file_path.name}")
        except IOError as e:
            logging.error(f"Failed to write file for {name}: {e}")

    logging.info(f"Successfully generated {count} invites in {OUTPUT_DIR}")

if __name__ == "__main__":
    print("==========================================")
    print("   SQUAD BDAY INVITE GENERATOR [v3.2]     ")
    print("==========================================")
    perform_mail_merge()