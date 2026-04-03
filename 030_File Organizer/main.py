#Libraries

import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

#class for the file organizer application
class FileOrganizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MedOrganize - File Sorting Utility")
        self.root.geometry("500x450")
        self.root.resizable(False, False)

        
        self.bg_color = "#f8fafc"
        self.accent_color = "#0ea5e9"  # Medical Sky Blue
        self.header_color = "#0369a1"
        self.card_bg = "#ffffff"
        
        self.root.configure(bg=self.bg_color)

        # File Mappings
        self.extension_map = {
            'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'],
            'Documents': ['.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx', '.ppt', '.pptx', '.csv'],
            'Videos': ['.mp4', '.mov', '.avi', '.mkv', '.wmv'],
            'Audio': ['.mp3', '.wav', '.flac', '.m4a'],
            'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz'],
            'Executables': ['.exe', '.msi', '.app', '.dmg']
        }

        self.selected_path = tk.StringVar(value="No folder selected")
        self.setup_ui()

    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg=self.header_color, pady=20)
        header.pack(fill="x")
        
        tk.Label(header, text="📁 ORGANIZE", font=("Helvetica", 16, "bold"), 
                 bg=self.header_color, fg="white").pack()
        tk.Label(header, text="Automated Directory Sorting Utility", font=("Helvetica", 9), 
                 bg=self.header_color, fg="#bae6fd").pack()

        # Content Container
        content = tk.Frame(self.root, bg=self.bg_color, padx=30, pady=30)
        content.pack(fill="both", expand=True)

        # Selection Card
        tk.Label(content, text="TARGET DIRECTORY", font=("Helvetica", 9, "bold"), 
                 bg=self.bg_color, fg="#64748b").pack(anchor="w")
        
        path_frame = tk.Frame(content, bg=self.card_bg, bd=1, relief="solid", highlightthickness=0)
        path_frame.config(highlightbackground="#e2e8f0")
        path_frame.pack(fill="x", pady=(5, 20))

        self.path_label = tk.Label(path_frame, textvariable=self.selected_path, font=("Helvetica", 10), 
                                   bg=self.card_bg, fg="#334155", padx=10, pady=10, wraplength=350)
        self.path_label.pack(side="left", fill="x", expand=True)

        # Buttons
        btn_frame = tk.Frame(content, bg=self.bg_color)
        btn_frame.pack(fill="x", pady=10)

        self.browse_btn = tk.Button(btn_frame, text="BROWSE FOLDER", bg="#e2e8f0", fg="#475569",
                                    font=("Helvetica", 10, "bold"), bd=0, padx=20, pady=10,
                                    cursor="hand2", command=self.browse_folder)
        self.browse_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.organize_btn = tk.Button(btn_frame, text="ORGANIZE NOW", bg=self.accent_color, fg="white",
                                      font=("Helvetica", 10, "bold"), bd=0, padx=20, pady=10,
                                      cursor="hand2", command=self.organize_files)
        self.organize_btn.pack(side="left", expand=True, fill="x", padx=(5, 0))

        # Status Info
        self.status_label = tk.Label(content, text="Ready to clean up workspace.", font=("Helvetica", 9, "italic"),
                                     bg=self.bg_color, fg="#94a3b8", pady=20)
        self.status_label.pack()

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.selected_path.set(folder)
            self.status_label.config(text=f"Ready to organize folder.", fg="#0ea5e9")

    def organize_files(self):
        path = self.selected_path.get()
        if not os.path.exists(path) or path == "No folder selected":
            messagebox.showwarning("Selection Required", "Please select a valid folder first.")
            return

        moved_count = 0
        try:
            # Iterate through files in directory
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                
                # Skip if it's a directory
                if os.path.isdir(item_path):
                    continue
                
                # Get extension
                _, extension = os.path.splitext(item)
                extension = extension.lower()

                # Find destination folder
                destination_folder = "Others"
                for category, extensions in self.extension_map.items():
                    if extension in extensions:
                        destination_folder = category
                        break
                
                # Create folder if it doesn't exist
                dest_dir = os.path.join(path, destination_folder)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
                
                # Move the file
                shutil.move(item_path, os.path.join(dest_dir, item))
                moved_count += 1

            if moved_count > 0:
                self.status_label.config(text=f"Success! Organized {moved_count} files.", fg="#10b981")
                messagebox.showinfo("Done", f"Successfully organized {moved_count} files into categories.")
            else:
                self.status_label.config(text="No loose files found to organize.", fg="#f59e0b")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    # Simple styling to clean up buttons and inputs
    style = ttk.Style()
    style.theme_use('clam')
    app = FileOrganizerApp(root)
    root.mainloop()