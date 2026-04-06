import pyodbc
from tkinter import messagebox

class DataManager:
    """Handles data validation and persistence to MS SQL Server."""
    
    def __init__(self):
        # Configuration for MS SQL Server
        # Adjust 'DRIVER' if you have a different version installed
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
            # Connect to 'master' first to ensure the DB exists
            conn = pyodbc.connect(
                f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.server};DATABASE=master;Trusted_Connection=yes;',
                autocommit=True
            )
            cursor = conn.cursor()
            
            # Create Database if it doesn't exist
            cursor.execute(f"IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '{self.database}') CREATE DATABASE {self.database}")
            conn.close()

            # Connect to passwordsDB to create the table
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

        is_ok = messagebox.askokcancel(title=website, message=f"Details entered: \nEmail: {email} "
                                                            f"\nPassword: {password} \nSave to SQL Database?")
        if is_ok:
            try:
                conn = pyodbc.connect(self.connection_string)
                cursor = conn.cursor()
                
                # SQL Insert Query
                query = "INSERT INTO Passwords (website, email, password) VALUES (?, ?, ?)"
                cursor.execute(query, (website, email, password))
                
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                messagebox.showerror(title="Database Error", message=f"Could not save data: {e}")
                return False
        return False