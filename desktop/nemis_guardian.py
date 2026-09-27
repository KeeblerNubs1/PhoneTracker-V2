import tkinter as tk
from tkinter import ttk, messagebox
import requests

API = "http://127.0.0.1:8000"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NEMIS Guardian // Security Console")
        self.geometry("1100x650")
        self.configure(bg="#090d14")
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure("Treeview", background="#101722",
                             fieldbackground="#101722", foreground="#d7e2f0",
                             rowheight=28)
        self.style.configure("Treeview.Heading", background="#172235",
                             foreground="#78e6ff")
        self.style.configure("TButton", padding=8)
        self.build()
        self.refresh()

    def build(self):
        header = tk.Frame(self, bg="#090d14")
        header.pack(fill="x", padx=18, pady=16)
        tk.Label(header, text="NEMIS // GUARDIAN",
                 fg="#78e6ff", bg="#090d14",
                 font=("Consolas", 22, "bold")).pack(side="left")
        tk.Label(header, text="CONSENT-BASED DEVICE SECURITY",
                 fg="#7f8da3", bg="#090d14",
                 font=("Consolas", 10)).pack(side="left", padx=18)
        tk.Button(header, text="REFRESH", command=self.refresh,
                  bg="#172235", fg="#78e6ff", relief="flat").pack(side="right")

        self.tree = ttk.Treeview(self, columns=(
            "device","name","platform","last","battery","lat","lon"
        ), show="headings")
        for col, title, width in [
            ("device","DEVICE ID",170),("name","NAME",170),
            ("platform","PLATFORM",100),("last","LAST SEEN",180),
            ("battery","BATTERY",90),("lat","LAT",110),("lon","LON",110)]:
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width)
        self.tree.pack(fill="both", expand=True, padx=18, pady=10)

        bottom = tk.Frame(self, bg="#090d14")
        bottom.pack(fill="x", padx=18, pady=12)
        tk.Button(bottom, text="VIEW LOCATION HISTORY",
                  command=self.history, bg="#172235", fg="#78e6ff",
                  relief="flat").pack(side="left")

    def refresh(self):
        try:
            data = requests.get(API + "/devices", timeout=3).json()
            for x in self.tree.get_children():
                self.tree.delete(x)
            for d in data:
                self.tree.insert("", "end", values=(
                    d["device_id"], d["name"], d["platform"],
                    d["last_seen"] or "-", d["battery"] if d["battery"] is not None else "-",
                    d["latitude"] if d["latitude"] is not None else "-",
                    d["longitude"] if d["longitude"] is not None else "-"
                ))
        except Exception as e:
            messagebox.showerror("API Error", str(e))

    def history(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Select device", "Select a device first.")
            return
        device = self.tree.item(sel[0])["values"][0]
        data = requests.get(f"{API}/devices/{device}/locations", timeout=3).json()
        text = "\n".join(
            f'{x["timestamp"]}  {x["latitude"]:.6f}, {x["longitude"]:.6f}  ±{x["accuracy"]}m'
            for x in data
        ) or "No location history."
        win = tk.Toplevel(self)
        win.title(f"Location History // {device}")
        win.geometry("800x500")
        box = tk.Text(win, bg="#090d14", fg="#bfefff",
                      insertbackground="#bfefff", font=("Consolas", 10))
        box.pack(fill="both", expand=True)
        box.insert("1.0", text)
        box.config(state="disabled")

if __name__ == "__main__":
    App().mainloop()
