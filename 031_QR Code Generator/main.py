import tkinter as tk
from tkinter import messagebox
import pyodbc
import json
import socket
import sys
from datetime import datetime

# --- CONFIGURATION (matches your Healthcare app pattern) ---
PC_NAME = socket.gethostname()
DATABASE_NAME = "QRCodeVaultDB"
DRIVER = "{ODBC Driver 18 for SQL Server}"


# --- PURE PYTHON QR GENERATION ENGINE ---
class PureQR:
    def __init__(self):
        self.size = 21
        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.reserved = [[False for _ in range(self.size)] for _ in range(self.size)]

    def generate(self, data):
        self.grid = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.reserved = [[False for _ in range(self.size)] for _ in range(self.size)]
        self._add_finder_patterns()
        self._add_timing_patterns()
        self._add_dark_module()
        bit_string = self._encode_to_bits(data)
        self._fill_data(bit_string)
        self._apply_mask()
        self._add_format_info()
        return self.grid

    def _add_finder_patterns(self):
        locs = [(0, 0), (14, 0), (0, 14)]
        for r_off, c_off in locs:
            for r in range(7):
                for c in range(7):
                    val = 1 if (r == 0 or r == 6 or c == 0 or c == 6 or (2 <= r <= 4 and 2 <= c <= 4)) else 0
                    self._set_module(r + r_off, c + c_off, val, reserve=True)

    def _add_timing_patterns(self):
        for i in range(8, 13):
            self._set_module(6, i, 1 if i % 2 == 0 else 0, reserve=True)
            self._set_module(i, 6, 1 if i % 2 == 0 else 0, reserve=True)

    def _add_dark_module(self):
        self._set_module(13, 8, 1, reserve=True)

    def _encode_to_bits(self, data):
        bits = "0100" + format(len(data), '08b')
        for char in data:
            bits += format(ord(char), '08b')
        bits += "0000"
        while len(bits) % 8 != 0:
            bits += "0"
        return bits[:152].ljust(152, '0')

    def _fill_data(self, bits):
        bit_idx, up = 0, True
        for c in range(self.size - 1, -1, -2):
            if c == 6:
                c -= 1
            rows = range(self.size - 1, -1, -1) if up else range(self.size)
            for r in rows:
                for col in (c, c - 1):
                    if not self.reserved[r][col] and bit_idx < len(bits):
                        self.grid[r][col] = int(bits[bit_idx])
                        bit_idx += 1
            up = not up

    def _apply_mask(self):
        for r in range(self.size):
            for c in range(self.size):
                if not self.reserved[r][c] and (r + c) % 2 == 0:
                    self.grid[r][c] = 1 - self.grid[r][c]

    def _add_format_info(self):
        fmt = "101010000010010"
        for i, bit in enumerate(fmt):
            val = int(bit)
            if i < 6:
                self._set_module(8, i, val)
            elif i < 8:
                self._set_module(8, i + 1, val)

    def _set_module(self, r, c, val, reserve=False):
        if 0 <= r < 21 and 0 <= c < 21:
            self.grid[r][c] = val
            if reserve:
                self.reserved[r][c] = True


# --- MS SQL SERVER CONTROLLER (same pattern as HealthcareDataEngine) ---
class MSSQLManager:
    def __init__(self):
        self.conn = None
        self.cursor = None

        try:
            # Step 1: Connect to master and create DB if it doesn't exist
            # (exactly like your Healthcare app does it)
            master_str = (
                f"DRIVER={DRIVER};"
                f"SERVER={PC_NAME};"
                f"DATABASE=master;"
                f"Trusted_Connection=yes;"
                f"TrustServerCertificate=yes;"
            )
            cn_master = pyodbc.connect(master_str, autocommit=True)
            cn_master.cursor().execute(
                f"IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '{DATABASE_NAME}') "
                f"CREATE DATABASE {DATABASE_NAME}"
            )
            cn_master.close()

            # Step 2: Connect to the application database
            app_str = (
                f"DRIVER={DRIVER};"
                f"SERVER={PC_NAME};"
                f"DATABASE={DATABASE_NAME};"
                f"Trusted_Connection=yes;"
                f"TrustServerCertificate=yes;"
            )
            self.conn = pyodbc.connect(app_str)
            self.cursor = self.conn.cursor()
            self._init_db()

        except Exception as e:
            messagebox.showerror(
                "SQL Error",
                f"Connection failed: {e}\n\nCheck if SQL Server is running."
            )
            sys.exit()

    def _init_db(self):
        self.cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'QRCodeVault')
            CREATE TABLE QRCodeVault (
                ID           INT PRIMARY KEY IDENTITY(1,1),
                URL          NVARCHAR(500) UNIQUE,
                QRMatrixJSON NVARCHAR(MAX),
                CreatedAt    DATETIME DEFAULT GETDATE()
            )
        """)
        self.conn.commit()

    def save_qr(self, url, matrix):
        matrix_json = json.dumps(matrix)
        try:
            self.cursor.execute("""
                MERGE INTO QRCodeVault AS Target
                USING (SELECT ? AS URL, ? AS JSON) AS Source
                ON Target.URL = Source.URL
                WHEN MATCHED THEN
                    UPDATE SET QRMatrixJSON = Source.JSON, CreatedAt = GETDATE()
                WHEN NOT MATCHED THEN
                    INSERT (URL, QRMatrixJSON) VALUES (Source.URL, Source.JSON);
            """, (url, matrix_json))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"SQL Save Error: {e}")
            return False

    def find_qr(self, search_term):
        try:
            self.cursor.execute(
                "SELECT TOP 1 URL, QRMatrixJSON, CreatedAt "
                "FROM QRCodeVault WHERE URL LIKE ? ORDER BY CreatedAt DESC",
                (f"%{search_term}%",)
            )
            return self.cursor.fetchone()
        except Exception as e:
            print(f"SQL Search Error: {e}")
            return None

    def close(self):
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass


# --- UI APPLICATION ---
class QRApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"MS SQL QR Vault — {PC_NAME}")
        self.root.geometry("500x720")
        self.root.configure(bg="#1a1a1a")

        self.db = MSSQLManager()   # exits via sys.exit() if connection fails
        self.qr = PureQR()

        self.setup_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def setup_ui(self):
        # Header
        tk.Label(self.root, text="MS SQL QR VAULT", font=("Arial", 16, "bold"),
                 bg="#1a1a1a", fg="#00ffcc").pack(pady=20)

        tk.Label(self.root, text=f"● Connected  •  {PC_NAME}  •  {DATABASE_NAME}",
                 font=("Arial", 9), bg="#1a1a1a", fg="#00ffcc").pack()

        # Input
        self.entry = tk.Entry(self.root, font=("Consolas", 12), width=40,
                              bg="#333", fg="white", insertbackground="white")
        self.entry.pack(pady=15)

        # Buttons
        btn_frame = tk.Frame(self.root, bg="#1a1a1a")
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Generate & Store", command=self.generate,
                  bg="#0078d4", fg="white", width=15, height=2).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Search DB", command=self.search,
                  bg="#2b88d8", fg="white", width=15, height=2).pack(side="left", padx=5)

        # Status
        self.status = tk.Label(self.root, text="Enter a URL or text above.",
                               bg="#1a1a1a", fg="gray", wraplength=460, font=("Arial", 10))
        self.status.pack(pady=8)

        # QR Canvas
        self.canvas = tk.Canvas(self.root, width=300, height=300, bg="white")
        self.canvas.pack(pady=15)

    def draw_qr(self, matrix):
        self.canvas.delete("all")
        size = 300 // 21
        for r in range(21):
            for c in range(21):
                if matrix[r][c] == 1:
                    self.canvas.create_rectangle(
                        c * size, r * size,
                        (c + 1) * size, (r + 1) * size,
                        fill="black", outline=""
                    )

    def generate(self):
        url = self.entry.get().strip()
        if not url:
            self.status.config(text="Please enter a URL or text.", fg="orange")
            return

        matrix = self.qr.generate(url)
        if self.db.save_qr(url, matrix):
            self.draw_qr(matrix)
            self.status.config(text="Saved to MS SQL Server!", fg="#00ffcc")
        else:
            self.status.config(text="SQL Error: Could not save. Check console.", fg="red")

    def search(self):
        term = self.entry.get().strip()
        if not term:
            self.status.config(text="Please enter a search term.", fg="orange")
            return

        row = self.db.find_qr(term)
        if row:
            url, matrix_json, created = row[0], row[1], row[2]
            matrix = json.loads(matrix_json)
            self.draw_qr(matrix)
            self.entry.delete(0, tk.END)
            self.entry.insert(0, url)
            # Handle both datetime object and string (varies by pyodbc version)
            date_str = created.strftime("%Y-%m-%d %H:%M") if isinstance(created, datetime) else str(created)
            self.status.config(text=f"Found! Saved on: {date_str}", fg="#00ffcc")
        else:
            self.status.config(text="No match found in MS SQL.", fg="orange")

    def _on_close(self):
        self.db.close()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = QRApp(root)
    root.mainloop()