#Libraries

import tkinter as tk
from tkinter import ttk
import random
import time
import math

#class SearchVisualizer:
class AdvancedSearchVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Algorithm Skill Server: Search Complexity Lab")
        self.root.geometry("1000x950")  # BUG FIX 1: Was "1000躍950" (corrupt Unicode char)
        self.root.configure(bg="#0f172a")

        # State
        self.data = []
        self.array_size = 25
        self.is_searching = False
        self.delay = 0.2

        # Algorithm Meta-Knowledge
        self.algo_info = {
            "linear": {
                "name": "Linear Search",
                "logic": "Checks every single item one by one from start to finish.",
                "best_for": "Small lists or UN-SORTED data where order is random.",
                "verdict": "Inefficient for large data, but universal.",
                "color": "#ef4444"
            },
            "binary": {
                "name": "Binary Search",
                "logic": "Splits the sorted list in half repeatedly until the target is found.",
                "best_for": "Large, SORTED datasets. This is the industry standard.",
                "verdict": "Extremely fast. The go-to algorithm for efficiency.",
                "color": "#3b82f6"
            },
            "jump": {
                "name": "Jump Search",
                "logic": "Skips fixed blocks (√n) then performs a short linear scan.",
                "best_for": "Systems where 'backwards' movement is expensive (like old tapes).",
                "verdict": "Faster than Linear, slower than Binary.",
                "color": "#a855f7"
            },
            "interpolation": {
                "name": "Interpolation Search",
                "logic": "Guesses the position based on values (like looking for 'Z' at the end of a book).",
                "best_for": "Uniformly distributed data (numbers spaced evenly).",
                "verdict": "Can beat Binary Search on specific data, but fails on clusters.",
                "color": "#10b981"
            }
        }

        self.setup_ui()
        self.generate_new_array()

    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg="#1e293b", pady=10)
        header.pack(fill="x")
        tk.Label(header, text="Search Algorithm Lab", font=("Segoe UI", 18, "bold"),
                 bg="#1e293b", fg="#38bdf8").pack()

        # Control Panel
        controls = tk.Frame(self.root, bg="#0f172a", pady=10)
        controls.pack()

        # Target Input
        tk.Label(controls, text="Target:", bg="#0f172a", fg="white").grid(row=0, column=0)
        self.target_entry = tk.Entry(controls, width=8, font=("Consolas", 12))
        self.target_entry.grid(row=0, column=1, padx=5)
        self.target_entry.insert(0, "50")

        # Buttons
        for i, (key, info) in enumerate(self.algo_info.items()):
            tk.Button(controls, text=info['name'], bg=info['color'], fg="white",
                      font=("Arial", 9, "bold"),
                      command=lambda k=key: self.run_search(k)).grid(row=0, column=i + 2, padx=3)

        tk.Button(controls, text="New Array", command=self.generate_new_array,
                  bg="#475569", fg="white").grid(row=0, column=6, padx=10)

        # Canvas
        self.canvas = tk.Canvas(self.root, width=900, height=250, bg="#1e293b", highlightthickness=0)
        self.canvas.pack(pady=5)

        # Stats & Complexity Row
        stats_row = tk.Frame(self.root, bg="#0f172a")
        stats_row.pack(fill="x", padx=40)

        self.stats_label = tk.Label(stats_row, text="Steps: 0", font=("Consolas", 14, "bold"),
                                    bg="#0f172a", fg="#fbbf24")
        self.stats_label.pack(side="left")

        self.actual_comp_label = tk.Label(stats_row, text="Complexity: -", bg="#0f172a",
                                          fg="#94a3b8", font=("Consolas", 10))
        self.actual_comp_label.pack(side="right")

    self.result_frame = tk.Frame(self.root, bg="#0f172a", pady=6)
        self.result_frame.pack(fill="x", padx=40)

        self.result_label = tk.Label(
            self.result_frame,
            text="",
            font=("Segoe UI", 13, "bold"),
            bg="#0f172a",
            fg="white",
            anchor="center"
        )
        self.result_label.pack(fill="x")


        self.info_panel = tk.LabelFrame(self.root, text=" Algorithm Encyclopedia ",
                                        bg="#1e293b", fg="#7dd3fc", padx=15, pady=10)
        self.info_panel.pack(fill="x", padx=40, pady=10)

        self.name_display = tk.Label(self.info_panel,
                                     text="Select an algorithm above to see how it works...",
                                     font=("Arial", 12, "bold"), bg="#1e293b", fg="white")
        self.name_display.pack(anchor="w")

        self.logic_display = tk.Label(self.info_panel, text="", font=("Arial", 10),
                                      bg="#1e293b", fg="#cbd5e1", wraplength=850, justify="left")
        self.logic_display.pack(anchor="w", pady=2)

        self.best_for_display = tk.Label(self.info_panel, text="", font=("Arial", 10, "italic"),
                                         bg="#1e293b", fg="#94a3b8")
        self.best_for_display.pack(anchor="w")


        self.verdict_frame = tk.Frame(self.root, bg="#083344", padx=15, pady=8)
        self.verdict_frame.pack(fill="x", padx=40)

        tk.Label(self.verdict_frame, text="PRO TIP:", font=("Arial", 9, "bold"),
                 bg="#083344", fg="#22d3ee").pack(side="left")
        self.verdict_label = tk.Label(
            self.verdict_frame,
            text="Binary Search is generally the 'King' of searching if your data is sorted.",
            bg="#083344", fg="white", font=("Arial", 10)
        )
        self.verdict_label.pack(side="left", padx=10)

    def generate_new_array(self):
        if self.is_searching:
            return
        self.data = sorted(random.sample(range(1, 200), self.array_size))
        self.draw_array()
        self.stats_label.config(text="Steps: 0")
        self.result_label.config(text="")  # Clear result on new array

    def draw_array(self, highlights={}):
        self.canvas.delete("all")
        c_width, c_height = 900, 250
        bar_width = c_width // self.array_size
        max_val = max(self.data)

        for i, val in enumerate(self.data):
            x0, x1 = i * bar_width + 4, (i + 1) * bar_width - 4
            h = (val / max_val) * (c_height - 60)
            y0, y1 = c_height - h - 30, c_height - 30
            color = highlights.get(i, "#334155")
            self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")
            self.canvas.create_text((x0 + x1) / 2, y1 + 15, text=str(val),
                                    fill="white", font=("Consolas", 8))

    def update_info(self, key, steps):
        info = self.algo_info[key]
        self.name_display.config(text=info['name'], fg=info['color'])
        self.logic_display.config(text=f"How it works: {info['logic']}")
        self.best_for_display.config(text=f"Best for: {info['best_for']}")
        self.verdict_label.config(text=info['verdict'])

        n = self.array_size
        if key == "linear":
            comp = "O(n) - Linear Time"
        elif key == "binary":
            comp = "O(log n) - Logarithmic Time (Max steps: ~5)"
        elif key == "jump":
            comp = "O(√n) - Root Time (Max steps: ~10)"
        else:
            comp = "O(log log n) - Distributed Time"

        self.actual_comp_label.config(text=f"Theoretical: {comp} | Total Steps: {steps}")

    def show_result(self, found, target, steps, algo_name):
        """BUG FIX 2: New method to display a clear found/not-found message."""
        if found:
            self.result_label.config(
                text=f"Target {target} FOUND in {steps} step(s) using {algo_name}!",
                fg="#22c55e"
            )
        else:
            self.result_label.config(
                text=f" Target {target} NOT FOUND in the array after {steps} step(s) using {algo_name}.",
                fg="#f87171"
            )

    def run_search(self, mode):
        if self.is_searching:
            return
        try:
            target = int(self.target_entry.get())
        except ValueError:
            self.result_label.config(text="⚠️  Please enter a valid integer as the target.", fg="#fbbf24")
            return
        self.result_label.config(text="🔍 Searching...", fg="#94a3b8")
        self.is_searching = True
        getattr(self, f"exec_{mode}")(target)
        self.is_searching = False

    def viz(self, mode, steps, highlights):
        self.stats_label.config(text=f"Steps: {steps}")
        self.update_info(mode, steps)
        self.draw_array(highlights)
        self.root.update()
        time.sleep(self.delay)

    def exec_linear(self, target):
        algo_name = self.algo_info["linear"]["name"]
        for i in range(len(self.data)):
            if self.data[i] == target:
                self.viz("linear", i + 1, {i: "#22c55e"})
                self.show_result(True, target, i + 1, algo_name)
                return
            self.viz("linear", i + 1, {i: "#ef4444"})
    
        self.show_result(False, target, len(self.data), algo_name)

    def exec_binary(self, target):
        algo_name = self.algo_info["binary"]["name"]
        low, high, steps = 0, len(self.data) - 1, 0
        while low <= high:
            steps += 1
            mid = (low + high) // 2
            self.viz("binary", steps, {mid: "#fbbf24", **{j: "#3b82f6" for j in range(low, high + 1)}})
            if self.data[mid] == target:
                self.viz("binary", steps, {mid: "#22c55e"})
                self.show_result(True, target, steps, algo_name)
                return
            if self.data[mid] < target:
                low = mid + 1
            else:
                high = mid - 1
    
        self.show_result(False, target, steps, algo_name)

    def exec_jump(self, target):
        algo_name = self.algo_info["jump"]["name"]
        n, steps = len(self.data), 0
        jump = int(math.sqrt(n))
        prev = 0

        
        while prev < n and self.data[min(jump, n) - 1] < target:
            steps += 1
            self.viz("jump", steps, {min(jump, n) - 1: "#a855f7"})
            prev = jump
            jump += int(math.sqrt(n))
            if prev >= n:
                break

        for i in range(prev, min(jump, n)):
            steps += 1
            if self.data[i] == target:
                self.viz("jump", steps, {i: "#22c55e"})
                self.show_result(True, target, steps, algo_name)
                return
            self.viz("jump", steps, {i: "#ef4444"})

        
        self.show_result(False, target, steps, algo_name)

    def exec_interpolation(self, target):
        algo_name = self.algo_info["interpolation"]["name"]
        low, high, steps = 0, len(self.data) - 1, 0

        while low <= high and target >= self.data[low] and target <= self.data[high]:
            steps += 1

            
            if self.data[high] == self.data[low]:
                if self.data[low] == target:
                    self.viz("interpolation", steps, {low: "#22c55e"})
                    self.show_result(True, target, steps, algo_name)
                    return
                break

            pos = low + ((target - self.data[low]) * (high - low)) // (self.data[high] - self.data[low])

            # Guard: clamp pos within valid bounds
            pos = max(low, min(pos, high))

            self.viz("interpolation", steps, {pos: "#fbbf24", **{j: "#10b981" for j in range(low, high + 1)}})

            if self.data[pos] == target:
                self.viz("interpolation", steps, {pos: "#22c55e"})
                self.show_result(True, target, steps, algo_name)
                return
            if self.data[pos] < target:
                low = pos + 1
            else:
                high = pos - 1

        
        self.show_result(False, target, steps, algo_name)


if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedSearchVisualizer(root)
    root.mainloop()