from tkinter import *
from tkinter import messagebox
from password_generator import PasswordGenerator
from data_manager import DataManager

class PasswordApp:
    def __init__(self, root):
        self.root = root
        self.root.title("My Password Manager")
        self.root.config(padx=50, pady=50)

        self.engine = PasswordGenerator()
        self.db = DataManager()

        # Canvas for Logo
        self.canvas = Canvas(height=200, width=200)
        # Assuming logo.png exists in the same folder
        try:
            self.logo_img = PhotoImage(file="logo.png")
            self.canvas.create_image(100, 100, image=self.logo_img)
        except:
            self.canvas.create_text(100, 100, text="LOGO", font=("Arial", 24, "bold"))
        self.canvas.grid(row=0, column=1)

        # Labels
        Label(text="Website:").grid(row=1, column=0)
        Label(text="Email/Username:").grid(row=2, column=0)
        Label(text="Password:").grid(row=3, column=0)

        # Entries
        self.website_entry = Entry(width=33)
        self.website_entry.grid(row=1, column=1)
        self.website_entry.focus()

        self.email_entry = Entry(width=52)
        self.email_entry.grid(row=2, column=1, columnspan=2)
        self.email_entry.insert(0, "user@example.com")

        self.password_entry = Entry(width=33)
        self.password_entry.grid(row=3, column=1)

        # Buttons
        self.search_button = Button(text="Search", width=14, command=self.find_password)
        self.search_button.grid(row=1, column=2)

        self.generate_password_button = Button(text="Generate Password", command=self.generate_password)
        self.generate_password_button.grid(row=3, column=2)

        self.add_button = Button(text="Add", width=44, command=self.save)
        self.add_button.grid(row=4, column=1, columnspan=2)

    def generate_password(self):
        self.password_entry.delete(0, END)
        new_password = self.engine.generate()
        self.password_entry.insert(0, new_password)

    def find_password(self):
        website = self.website_entry.get()
        self.db.search_entry(website)

    def save(self):
        website = self.website_entry.get()
        email = self.email_entry.get()
        password = self.password_entry.get()

        if self.db.save_entry(website, email, password):
            self.website_entry.delete(0, END)
            self.password_entry.delete(0, END)

if __name__ == "__main__":
    root = Tk()
    app = PasswordApp(root)
    root.mainloop()