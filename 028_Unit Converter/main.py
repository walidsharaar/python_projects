import tkinter as tk
from tkinter import ttk

class UnitConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("UnitConvert - Unit Conversion Utility")
        self.root.geometry("400x550")
        
     
        self.bg_primary = "#f0f9ff"  
        self.accent_color = "#0891b2" 
        self.text_color = "#1e293b"
        self.card_bg = "#ffffff"
        
        self.root.configure(bg=self.bg_primary)

        # Header
        header_frame = tk.Frame(self.root, bg=self.accent_color, pady=20)
        header_frame.pack(fill="x")
        
        tk.Label(header_frame, text="✚ UNITCONVERT", font=("Helvetica", 16, "bold"), 
                 bg=self.accent_color, fg="white").pack()
        tk.Label(header_frame, text=" Unit Conversion Utility", font=("Helvetica", 9), 
                 bg=self.accent_color, fg="#cffafe").pack()

        # Main Container
        self.main_frame = tk.Frame(self.root, bg=self.bg_primary, padx=30, pady=20)
        self.main_frame.pack(fill="both", expand=True)

        # Conversion Data
        # Format: {Category: {Unit: multiplier_to_base}}
        # Base units: Length(m), Weight(kg), Volume(ml), Temp(special logic)
        self.categories = {
            "Weight (Patient)": {"kg": 1, "grams": 0.001, "lbs": 0.453592, "oz": 0.0283495},
            "Liquid (Dosage)": {"ml": 1, "cc": 1, "liters": 1000, "tsp": 4.92892, "tbsp": 14.7868, "oz (fl)": 29.5735},
            "Length (Height)": {"cm": 1, "meters": 100, "inches": 2.54, "feet": 30.48}
        }

        self.setup_ui()

    def setup_ui(self):
        # 1. Category Selection
        self.label_style = {"bg": self.bg_primary, "fg": "#64748b", "font": ("Helvetica", 10, "bold")}
        
        tk.Label(self.main_frame, text="SELECT CATEGORY", **self.label_style).pack(anchor="w", pady=(0, 5))
        self.cat_var = tk.StringVar(value="Weight (Patient)")
        self.cat_combo = ttk.Combobox(self.main_frame, textvariable=self.cat_var, 
                                      values=list(self.categories.keys()), state="readonly", font=("Helvetica", 11))
        self.cat_combo.pack(fill="x", pady=(0, 20))
        self.cat_combo.bind("<<ComboboxSelected>>", self.refresh_units)

        # 2. Input Value
        tk.Label(self.main_frame, text="ENTER VALUE", **self.label_style).pack(anchor="w", pady=(0, 5))
        self.input_entry = tk.Entry(self.main_frame, font=("Helvetica", 14), bd=0, highlightthickness=1, 
                                    highlightbackground="#cbd5e1", bg=self.card_bg)
        self.input_entry.pack(fill="x", pady=(0, 20), ipady=8)
        self.input_entry.insert(0, "0")

        # 3. From/To Units
        unit_frame = tk.Frame(self.main_frame, bg=self.bg_primary)
        unit_frame.pack(fill="x", pady=(0, 20))

        # From
        from_container = tk.Frame(unit_frame, bg=self.bg_primary)
        from_container.pack(side="left", expand=True, fill="x", padx=(0, 10))
        tk.Label(from_container, text="FROM", **self.label_style).pack(anchor="w")
        self.from_var = tk.StringVar()
        self.from_combo = ttk.Combobox(from_container, textvariable=self.from_var, state="readonly")
        self.from_combo.pack(fill="x")

        # To
        to_container = tk.Frame(unit_frame, bg=self.bg_primary)
        to_container.pack(side="left", expand=True, fill="x", padx=(10, 0))
        tk.Label(to_container, text="TO", **self.label_style).pack(anchor="w")
        self.to_var = tk.StringVar()
        self.to_combo = ttk.Combobox(to_container, textvariable=self.to_var, state="readonly")
        self.to_combo.pack(fill="x")

        # 4. Convert Button
        self.convert_btn = tk.Button(self.main_frame, text="CALCULATE METRIC", bg=self.accent_color, fg="white",
                                     font=("Helvetica", 11, "bold"), bd=0, cursor="hand2", 
                                     activebackground="#0e7490", command=self.convert)
        self.convert_btn.pack(fill="x", pady=10, ipady=12)

        # 5. Result Display
        self.result_card = tk.Frame(self.main_frame, bg="#ecfeff", bd=1, relief="flat", highlightthickness=1, highlightbackground="#a5f3fc")
        self.result_card.pack(fill="x", pady=20, ipady=15)
        
        self.result_label = tk.Label(self.result_card, text="---", font=("Helvetica", 14, "bold"), 
                                     bg="#ecfeff", fg=self.accent_color)
        self.result_label.pack(expand=True)

        self.refresh_units()

    def refresh_units(self, event=None):
        cat = self.cat_var.get()
        units = list(self.categories[cat].keys())
        self.from_combo['values'] = units
        self.to_combo['values'] = units
        self.from_var.set(units[0])
        self.to_var.set(units[1] if len(units) > 1 else units[0])

    def convert(self):
        try:
            raw_val = self.input_entry.get().strip()
            if not raw_val: return
            
            value = float(raw_val)
            cat = self.cat_var.get()
            u_from = self.from_var.get()
            u_to = self.to_var.get()

            # Logic: Convert to base, then to target
            base_val = value * self.categories[cat][u_from]
            result = base_val / self.categories[cat][u_to]

            # Formatting
            if result < 0.001:
                display_res = f"{result:.6f}"
            else:
                display_res = f"{result:,.3f}"

            self.result_label.config(text=f"{display_res} {u_to}", fg=self.accent_color)
        except ValueError:
            self.result_label.config(text="Invalid Input", fg="#ef4444")

if __name__ == "__main__":
    root = tk.Tk()
    # Simple styling for Combobox
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("TCombobox", fieldbackground="white", background="#cbd5e1")
    
    app = UnitConverter(root)
    root.mainloop()