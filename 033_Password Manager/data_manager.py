import pyodbc
from tkinter import messagebox

class DataManager:
    """Handles data validation, persistence, and searching in MS SQL Server."""
    
    def __init__(self):
        self.server = 'localhost' 
        self.database = 'passwordsDB'
        self.connection_string = (
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={self.server};'
            f'DATABASE={self.database};'
            f'Trusted_Connection=yes;'
        )
        self.init_db()

    def init_db(self):
        """Creates the database and table if they don't exist."""
        try:
            conn = pyodbc.connect(
                f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.server};DATABASE=master;Trusted_Connection=yes;',
                autocommit=True
            )
            cursor = conn.cursor()
            cursor.execute(f"IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '{self.database}') CREATE DATABASE {self.database}")
            conn.close()

            conn = pyodbc.connect(self.connection_string, autocommit=True)
            cursor = conn.cursor()
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Passwords]') AND type in (N'U'))
                CREATE TABLE Passwords (
                    id INT PRIMARY KEY IDENTITY(1,1),
                    website NVARCHAR(255),
                    email NVARCHAR(255),
                    password NVARCHAR(255),
                    created_at DATETIME DEFAULT GETDATE()
                )
            """)
            conn.close()
        except Exception as e:
            print(f"Database Initialization Error: {e}")

    def save_entry(self, website, email, password):
        """Validates inputs and saves to MS SQL Server table."""
        if len(website) == 0 or len(password) == 0:
            messagebox.showinfo(title="Oops", message="Please don't leave any fields empty!")
            return False

        try:
            conn = pyodbc.connect(self.connection_string)
            cursor = conn.cursor()
            query = "INSERT INTO Passwords (website, email, password) VALUES (?, ?, ?)"
            cursor.execute(query, (website, email, password))
            conn.commit()
            conn.close()
            messagebox.showinfo(title="Success", message=f"Details for {website} saved successfully.")
            return True
        except Exception as e:
            messagebox.showerror(title="Database Error", message=f"Could not save data: {e}")
            return False

    def search_entry(self, searchTerm):
        """Searches for entries by website name or email using SQL LIKE."""
        if len(searchTerm) == 0:
            messagebox.showinfo(title="Error", message="Please enter a website or email to search.")
            return

        try:
            conn = pyodbc.connect(self.connection_string)
            cursor = conn.cursor()
            # Search both website and email columns
            query = "SELECT website, email, password FROM Passwords WHERE website LIKE ? OR email LIKE ?"
            cursor.execute(query, (f'%{searchTerm}%', f'%{searchTerm}%'))
            results = cursor.fetchall()
            conn.close()

            if results:
                message_text = ""
                for row in results:
                    message_text += f"Website: {row.website}\nEmail: {row.email}\nPassword: {row.password}\n----------\n"
                messagebox.showinfo(title=f"Results for '{searchTerm}'", message=message_text)
            else:
                messagebox.showinfo(title="Not Found", message=f"No entries found for '{searchTerm}'.")
        except Exception as e:
            messagebox.showerror(title="Database Error", message=f"Search failed: {e}")