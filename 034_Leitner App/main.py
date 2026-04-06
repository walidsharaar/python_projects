import tkinter as tk
from tkinter import messagebox
import config
from database import DatabaseManager
from engine import LeitnerEngine

class LeitnerAppUI:
    """
    The main UI controller for the German Leitner System.
    Coordinates between the user interface and the business logic.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("German Leitner Trainer")
        self.root.geometry("550x550")
        self.root.configure(bg=config.COLORS['bg'])

        # 1. Initialize Backend
        self.db_manager = DatabaseManager()
        if not self.db_manager.setup_database():
            messagebox.showerror("Database Error", "Could not connect to MS SQL Server. Check your connection string in config.py.")
            self.root.destroy()
            return
            
        self.engine = LeitnerEngine(self.db_manager)

        # 2. Local State
        self.review_queue = []
        self.current_word = None

        # 3. Build Interface
        self._setup_ui()

    def _setup_ui(self):
        # --- Add New Vocabulary Section ---
        add_frame = tk.LabelFrame(self.root, text="Add New German Phrase", bg=config.COLORS['bg'], padx=15, pady=15)
        add_frame.pack(fill="x", padx=20, pady=15)

        tk.Label(add_frame, text="German:", bg=config.COLORS['bg']).grid(row=0, column=0, sticky="w")
        self.de_entry = tk.Entry(add_frame, width=30, font=("Helvetica", 10))
        self.de_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(add_frame, text="English:", bg=config.COLORS['bg']).grid(row=1, column=0, sticky="w")
        self.en_entry = tk.Entry(add_frame, width=30, font=("Helvetica", 10))
        self.en_entry.grid(row=1, column=1, padx=10, pady=5)

        self.btn_save = tk.Button(add_frame, text="Add Word", bg=config.COLORS['accent'], fg="white", 
                                 font=("Helvetica", 10, "bold"), command=self.handle_add)
        self.btn_save.grid(row=0, column=2, rowspan=2, padx=10, sticky="ns")

        # --- Study Session Section ---
        self.study_frame = tk.Frame(self.root, bg="white", highlightbackground="#cccccc", highlightthickness=1)
        self.study_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.display_label = tk.Label(self.study_frame, text="Ready to learn?", font=("Helvetica", 20, "bold"), 
                                      bg="white", fg=config.COLORS['text'], wraplength=450)
        self.display_label.pack(expand=True)

        # --- Control Buttons ---
        btn_frame = tk.Frame(self.root, bg=config.COLORS['bg'])
        btn_frame.pack(fill="x", padx=20, pady=20)

        self.btn_start = tk.Button(btn_frame, text="Start Session", height=2, width=15, 
                                   command=self.start_review)
        self.btn_start.pack(side="left", padx=5)

        self.btn_reveal = tk.Button(btn_frame, text="Show Answer", height=2, width=15, 
                                    state="disabled", command=self.handle_reveal)
        self.btn_reveal.pack(side="left", padx=5)

    def handle_add(self):
        de = self.de_entry.get().strip()
        en = self.en_entry.get().strip()
        if de and en:
            self.engine.add_vocabulary(de, en)
            self.de_entry.delete(0, tk.END)
            self.en_entry.delete(0, tk.END)
            messagebox.showinfo("Success", f"'{de}' is now in Box 1.")
        else:
            messagebox.showwarning("Warning", "Please provide both the German and English text.")

    def start_review(self):
        self.review_queue = self.engine.get_due_words()
        if not self.review_queue:
            self.display_label.config(text="No words due for review!\nCome back later. 🎉", fg=config.COLORS['primary'])
            return
        
        self.btn_start.config(state="disabled")
        self._next_card()

    def _next_card(self):
        if self.review_queue:
            self.current_word = self.review_queue.pop(0)
            self.display_label.config(text=self.current_word['german'], fg=config.COLORS['text'])
            self.btn_reveal.config(state="normal")
        else:
            self.display_label.config(text="Session Complete!", fg=config.COLORS['accent'])
            self.btn_start.config(state="normal")
            self.btn_reveal.config(state="disabled")

    def handle_reveal(self):
        # Display the translation and ask the user for their self-assessment
        is_correct = messagebox.askyesno("Leitner Check", 
                                         f"German: {self.current_word['german']}\n"
                                         f"English: {self.current_word['english']}\n\n"
                                         "Did you get it right?")
        
        # Update the database via the engine
        self.engine.update_word_progress(self.current_word['id'], self.current_word['box'], is_correct)
        self._next_card()

if __name__ == "__main__":
    root = tk.Tk()
    app = LeitnerAppUI(root)
    root.mainloop()