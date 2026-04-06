from tkinter import *
from password_generator import PasswordGenerator
from data_manager import DataManager

class PasswordManagerApp:
    """Main Class that manages the GUI and coordinates the engine and data manager."""
    def __init__(self):
        self.window = Tk()
        self.window.title("Password Manager")
        self.window.config(padx=50, pady=50)

        # Initialize Helper Classes (Composition)
        self.generator = PasswordGenerator()
        self.data_manager = DataManager()

        self.setup_ui()
        self.window.mainloop()

    def setup_ui(self):
        """Creates and layouts all the UI components."""
        # Canvas for Image/Logo
        self.canvas = Canvas(height=200, width=200)
        # Note: In a local environment, you'd use PhotoImage here
        self.canvas.create_text(100, 100, text="🔐", font=("Arial", 80))
        self.canvas.grid(row=0, column=1)

        # Labels
        self.website_label = Label(text="Website:")
        self.website_label.grid(row=1, column=0)
        self.email_label = Label(text="Email/Username:")
        self.email_label.grid(row=2, column=0)
        self.password_label = Label(text="Password:")
        self.password_label.grid(row=3, column=0)

        # Entries
        self.website_entry = Entry(width=35)
        self.website_entry.grid(row=1, column=1, columnspan=2, sticky="EW")
        self.website_entry.focus()
        
        self.email_entry = Entry(width=35)
        self.email_entry.grid(row=2, column=1, columnspan=2, sticky="EW")
        self.email_entry.insert(0, "user@email.com")
        
        self.password_entry = Entry(width=21)
        self.password_entry.grid(row=3, column=1, sticky="EW")

        # Buttons
        self.generate_password_button = Button(text="Generate Password", command=self.create_password)
        self.generate_password_button.grid(row=3, column=2, sticky="EW")
        
        self.add_button = Button(text="Add", width=36, command=self.save)
        self.add_button.grid(row=4, column=1, columnspan=2, sticky="EW")

    def create_password(self):
        """Interaction logic to generate and display a password."""
        new_pass = self.generator.generate()
        self.password_entry.delete(0, END)
        self.password_entry.insert(0, new_pass)

    def save(self):
        """Interaction logic to send data to the manager and clear the UI."""
        website = self.website_entry.get()
        email = self.email_entry.get()
        password = self.password_entry.get()

        success = self.data_manager.save_entry(website, email, password)
        
        if success:
            self.website_entry.delete(0, END)
            self.password_entry.delete(0, END)

if __name__ == "__main__":
    PasswordManagerApp()