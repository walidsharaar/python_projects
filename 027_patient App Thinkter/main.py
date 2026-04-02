#libraries
import tkinter as tk
from tkinter import ttk, messagebox
import pyodbc
import sys
import socket
from datetime import datetime

# --- 1. CONFIGURATION ---
PC_NAME = socket.gethostname()
DATABASE_NAME = 'HealthcareDB'

class PlaceholderEntry(tk.Entry):
    """Custom Entry widget with ghost-text placeholders."""
    def __init__(self, master=None, placeholder="PLACEHOLDER", color='grey', **kwargs):
        super().__init__(master, **kwargs)
        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self['fg']
        self.bind("<FocusIn>", self._clear_placeholder)
        self.bind("<FocusOut>", self._add_placeholder)
        self._add_placeholder()

    def _add_placeholder(self, e=None):
        if not self.get():
            self.insert(0, self.placeholder)
            self['fg'] = self.placeholder_color

    def _clear_placeholder(self, e=None):
        if self['fg'] == self.placeholder_color:
            self.delete(0, tk.END)
            self['fg'] = self.default_fg_color

    def get_real_text(self):
        text = self.get()
        if self['fg'] == self.placeholder_color or text == self.placeholder:
            return ""
        return text

class HealthcareDataEngine:
    def __init__(self):
        self.conn = None
        self.cursor = None
        driver = "{ODBC Driver 18 for SQL Server}"
        server = PC_NAME 
        
        try:
            # Create Database if not exists
            m_str = f"DRIVER={driver};SERVER={server};DATABASE=master;Trusted_Connection=yes;TrustServerCertificate=yes;"
            cn_m = pyodbc.connect(m_str, autocommit=True)
            cn_m.cursor().execute(f"IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '{DATABASE_NAME}') CREATE DATABASE {DATABASE_NAME}")
            cn_m.close()
            
            # Connect to Application Database
            a_str = f"DRIVER={driver};SERVER={server};DATABASE={DATABASE_NAME};Trusted_Connection=yes;TrustServerCertificate=yes;"
            self.conn = pyodbc.connect(a_str)
            self.cursor = self.conn.cursor()
            self.init_schema()
        except Exception as e:
            messagebox.showerror("SQL Error", f"Connection failed: {e}\n\nCheck if SQL Server is running.")
            sys.exit()

    def init_schema(self):
        # Bronze Layer (Raw Payloads)
        self.cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Bronze_Layer')
            CREATE TABLE Bronze_Layer (Id INT IDENTITY(1,1) PRIMARY KEY, Payload NVARCHAR(MAX), TS DATETIME DEFAULT GETDATE())
        """)
        
        # Silver Layer (Structured Data)
        self.cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Silver_Layer')
            CREATE TABLE Silver_Layer (
                PatientId INT IDENTITY(1,1) PRIMARY KEY,
                FullName NVARCHAR(150),
                DOB DATE,
                Age INT,
                Gender NVARCHAR(20),
                BloodType NVARCHAR(5),
                ChiefIssue NVARCHAR(MAX),
                Doctor NVARCHAR(100),
                AdmitDate DATE,
                Room INT,
                BP NVARCHAR(20),
                Temp FLOAT,
                IsDischarged BIT DEFAULT 0
            )
        """)
        self.conn.commit()

    def push_to_bronze(self, d):
        payload = "|".join([f"{k}:::{v}" for k, v in d.items()])
        self.cursor.execute("INSERT INTO Bronze_Layer (Payload) VALUES (?)", (payload,))
        self.conn.commit()

    def process_to_silver(self):
        self.cursor.execute("SELECT Id, Payload FROM Bronze_Layer")
        rows = self.cursor.fetchall()
        count = 0
        for rid, raw in rows:
            try:
                p = dict(item.split(":::") for item in raw.split("|"))
                self.cursor.execute("""
                    INSERT INTO Silver_Layer (FullName, DOB, Age, Gender, BloodType, ChiefIssue, Doctor, AdmitDate, Room, BP, Temp, IsDischarged)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """, (p['NAME'], p['DOB'], int(p['AGE']), p['GEND'], p['BLOD'], p['ISSU'], p['DOCT'], p['ADMT'], int(p['ROOM']), p['BP'], float(p['TEMP'])))
                self.cursor.execute("DELETE FROM Bronze_Layer WHERE Id = ?", (rid,))
                count += 1
            except Exception as e: 
                print(f"ETL Error: {e}")
        self.conn.commit()
        return count
# Main Application
class HospitalApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Healthcare Management - {PC_NAME}")
        self.root.geometry("1000x750")
        self.root.configure(bg="#f8fafc")
        
        self.engine = HealthcareDataEngine()
        
        # State
        self.v_age = tk.StringVar(value="0")
        self.v_doctor = tk.StringVar(value="Dr. Ahmad Wali")
        self.v_gender = tk.StringVar(value="Male")

        self.setup_ui()
        self.refresh_table()
# UI Setup
    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#1e293b", height=60)
        header.pack(fill="x")
        tk.Label(header, text="PATIENT DATA ENTRY SYSTEM", font=("Segoe UI", 14, "bold"), fg="white", bg="#1e293b").pack(pady=15)

        main = tk.Frame(self.root, bg="#f8fafc", padx=20, pady=10)
        main.pack(fill="both", expand=True)

        # 1. Registration Form
        form = tk.LabelFrame(main, text=" Patient Information ", bg="white", padx=15, pady=15, font=("Arial", 10, "bold"))
        form.pack(fill="x", pady=10)

        # Name
        tk.Label(form, text="Full Name:", bg="white").grid(row=0, column=0, sticky="w")
        self.ent_name = PlaceholderEntry(form, placeholder="e.g. John Doe", width=25)
        self.ent_name.grid(row=0, column=1, padx=5, pady=5)

        # DOB & Age
        tk.Label(form, text="DOB (YYYY-MM-DD):", bg="white").grid(row=0, column=2, sticky="w")
        self.ent_dob = PlaceholderEntry(form, placeholder="1990-01-25", width=15)
        self.ent_dob.grid(row=0, column=3, padx=5)
        self.ent_dob.bind("<KeyRelease>", self.update_age)

        tk.Label(form, text="Age:", bg="white").grid(row=0, column=4, sticky="w")
        tk.Entry(form, textvariable=self.v_age, width=5, state="readonly").grid(row=0, column=5, padx=5)

        # Issue & Doctor
        tk.Label(form, text="Chief Issue:", bg="white").grid(row=1, column=0, sticky="w")
        self.ent_issue = PlaceholderEntry(form, placeholder="Reason for admission", width=25)
        self.ent_issue.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(form, text="Doctor:", bg="white").grid(row=1, column=2, sticky="w")
        ttk.Combobox(form, textvariable=self.v_doctor, values=["Dr. Ahmad Wali", "Dr. Sara Noori", "Dr. Karim Jafar"], width=13).grid(row=1, column=3, padx=5)

        # Gender & Room
        tk.Label(form, text="Gender:", bg="white").grid(row=1, column=4, sticky="w")
        ttk.Combobox(form, textvariable=self.v_gender, values=["Male", "Female", "Other"], width=5).grid(row=1, column=5, padx=5)

        tk.Label(form, text="Room #:", bg="white").grid(row=2, column=0, sticky="w")
        self.ent_room = PlaceholderEntry(form, placeholder="101", width=10)
        self.ent_room.grid(row=2, column=1, padx=5, pady=5)

        # Submit to Bronze
        tk.Button(form, text="INGEST RAW DATA (BRONZE)", bg="#f59e0b", fg="white", font=("Arial", 9, "bold"), command=self.on_submit, height=2).grid(row=3, column=0, columnspan=6, pady=10, sticky="we")

        # 2. Controls
        ctrls = tk.Frame(main, bg="#f8fafc")
        ctrls.pack(fill="x", pady=10)
        tk.Button(ctrls, text="RUN ETL PIPELINE (SYNC TO SILVER)", bg="#10b981", fg="white", font=("Arial", 10, "bold"), command=self.on_pipeline, height=2).pack(side="left", fill="x", expand=True, padx=5)
        tk.Button(ctrls, text="DISCHARGE PATIENT", bg="#ef4444", fg="white", font=("Arial", 10, "bold"), command=self.on_discharge, height=2).pack(side="right", padx=5)

        # 3. Data View
        self.tree = ttk.Treeview(main, columns=("ID", "Name", "Age", "Doctor", "Room"), show="headings")
        cfg = {"ID": 50, "Name": 250, "Age": 70, "Doctor": 200, "Room": 100}
        for c, w in cfg.items():
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, anchor="center")
        self.tree.pack(fill="both", expand=True)
# Age Calculation
    def update_age(self, event=None):
        dob_str = self.ent_dob.get_real_text()
        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d")
            today = datetime.now()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            self.v_age.set(str(max(0, age)))
        except:
            self.v_age.set("?")
#Submit to Bronze
    def on_submit(self):
        self.update_age()
        name = self.ent_name.get_real_text()
        dob = self.ent_dob.get_real_text()
        room = self.ent_room.get_real_text()
        
        if not name or not dob or not room.isdigit():
            messagebox.showerror("Invalid Input", "Please fill in Name, DOB (YYYY-MM-DD), and numeric Room #.")
            return

        data = {
            "NAME": name, "DOB": dob, "AGE": self.v_age.get(),
            "ISSU": self.ent_issue.get_real_text(), "DOCT": self.v_doctor.get(),
            "ADMT": datetime.now().strftime("%Y-%m-%d"), "ROOM": room,
            "BP": "120/80", "TEMP": "37.0", "BLOD": "O+", "GEND": self.v_gender.get()
        }
        
        self.engine.push_to_bronze(data)
        messagebox.showinfo("Success", "Raw payload staged in Bronze Layer.")
        
        # Reset
        for e in [self.ent_name, self.ent_dob, self.ent_issue, self.ent_room]:
            e.delete(0, tk.END)
            e._add_placeholder()
        self.v_age.set("0")
# ETL Pipeline
    def on_pipeline(self):
        count = self.engine.process_to_silver()
        self.refresh_table()
        messagebox.showinfo("Pipeline", f"Processed {count} records into Silver Layer.")
#Discharge Patient
    def on_discharge(self):
        sel = self.tree.selection()
        if not sel: return
        pid = self.tree.item(sel[0])['values'][0]
        if messagebox.askyesno("Confirm", "Discharge selected patient?"):
            self.engine.cursor.execute("UPDATE Silver_Layer SET IsDischarged = 1 WHERE PatientId = ?", (pid,))
            self.engine.conn.commit()
            self.refresh_table()
#Refresh Table
    def refresh_table(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        self.engine.cursor.execute("SELECT PatientId, FullName, Age, Doctor, Room FROM Silver_Layer WHERE IsDischarged = 0")
        for row in self.engine.cursor.fetchall():
            self.tree.insert("", "end", values=list(row))

if __name__ == "__main__":
    root = tk.Tk()
    app = HospitalApp(root)
    root.mainloop()