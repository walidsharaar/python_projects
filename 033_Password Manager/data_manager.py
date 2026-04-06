from tkinter import messagebox

class DataManager:
    """Handles data validation and file persistence."""
    def __init__(self, file_path="data.txt"):
        self.file_path = file_path

    def save_entry(self, website, email, password):
        """Validates inputs and saves to a local text file."""
        if len(website) == 0 or len(password) == 0:
            messagebox.showinfo(title="Oops", message="Please don't leave any fields empty!")
            return False

        is_ok = messagebox.askokcancel(title=website, message=f"Details entered: \nEmail: {email} "
                                                            f"\nPassword: {password} \nIs it ok to save?")
        if is_ok:
            with open(self.file_path, "a") as data_file:
                data_file.write(f"{website} | {email} | {password}\n")
            return True
        return False