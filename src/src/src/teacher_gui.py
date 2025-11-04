# src/teacher_gui.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from pathlib import Path
import sqlite3

BASE = Path(__file__).resolve().parents[1]
CSV_FILE = BASE / "attendance.csv"
DB_FILE = BASE / "attendance.sqlite3"

class TeacherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Attendance Reports")
        self.geometry("800x500")
        self.create_widgets()

    def create_widgets(self):
        toolbar = tk.Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        tk.Button(toolbar, text="Load CSV", command=self.load_csv).pack(side=tk.LEFT, padx=4, pady=4)
        tk.Button(toolbar, text="Load DB", command=self.load_db).pack(side=tk.LEFT, padx=4, pady=4)
        tk.Button(toolbar, text="Export CSV", command=self.export_csv).pack(side=tk.LEFT, padx=4, pady=4)

        cols = ("name","date","time","status")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c.title())
            self.tree.column(c, width=180)
        self.tree.pack(expand=True, fill=tk.BOTH)

    def load_csv(self):
        if not CSV_FILE.exists():
            messagebox.showinfo("Info", f"{CSV_FILE} not found")
            return
        df = pd.read_csv(CSV_FILE)
        self._show_df(df)

    def load_db(self):
        conn = sqlite3.connect(DB_FILE)
        df = pd.read_sql_query("SELECT name,date,time,status FROM attendance ORDER BY date DESC, time DESC", conn)
        conn.close()
        self._show_df(df)

    def _show_df(self, df):
        # clear
        for i in self.tree.get_children():
            self.tree.delete(i)
        for _, row in df.iterrows():
            self.tree.insert("", "end", values=(row["name"], row["date"], row["time"], row["status"]))

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv")
        if not path:
            return
        # try DB first
        try:
            conn = sqlite3.connect(DB_FILE)
            df = pd.read_sql_query("SELECT name,date,time,status FROM attendance", conn)
            conn.close()
            df.to_csv(path, index=False)
            messagebox.showinfo("Exported", f"Exported to {path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    app = TeacherApp()
    app.mainloop()
