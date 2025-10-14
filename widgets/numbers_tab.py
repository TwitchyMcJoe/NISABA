# widgets/numbers_tab.py
import os
from tkinter import ttk, messagebox
import tkinter as tk

from utils.file_io import load_csv, save_csv, ensure_language_dir
from constants import NUMBERS_FILE


def build_numbers_tab(app):
    """Attach the Numbers tab to the main notebook."""
    tab = ttk.Frame(app.notebook)
    app.notebook.add(tab, text="Numerology")

    ttk.Label(tab, text="Numerology",
              font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=10, pady=(8, 4))

    ctrl = ttk.Frame(tab); ctrl.pack(fill="x", padx=6, pady=6)
    ttk.Button(ctrl, text="Add Number", command=lambda: add_number(app)).pack(side="left", padx=4)
    ttk.Button(ctrl, text="Delete", command=lambda: delete_number(app)).pack(side="left", padx=4)
    ttk.Button(ctrl, text="Save", command=lambda: save_numbers(app)).pack(side="left", padx=4)
    ttk.Button(ctrl, text="Reload", command=lambda: load_numbers(app, app.current_language)).pack(side="left", padx=4)

    # Expanded Treeview with 4 columns
    app.numbers_tree = ttk.Treeview(
        tab,
        columns=("value", "word", "pronunciation", "symbol"),
        show="headings",
        height=16
    )
    headers = [
        ("value", "Value"),
        ("word", "Word"),
        ("pronunciation", "Pronunciation"),
        ("symbol", "Symbol")
    ]
    widths = [100, 160, 180, 100]
    for (col, txt), w in zip(headers, widths):
        app.numbers_tree.heading(col, text=txt)
        app.numbers_tree.column(col, width=w)

    app.numbers_tree.pack(fill="both", expand=True, padx=6, pady=6)
    from utils.table_edit import enable_treeview_editing
    enable_treeview_editing(app.numbers_tree)

    # Base conversion UI
    conv_frame = ttk.Frame(tab); conv_frame.pack(fill="x", padx=6, pady=6)

    ttk.Label(conv_frame, text="Convert Number:").pack(side="left", padx=4)
    app.base_input = tk.Entry(conv_frame, width=10)
    app.base_input.pack(side="left", padx=4)

    ttk.Label(conv_frame, text="From base").pack(side="left")
    app.base_from = tk.Entry(conv_frame, width=5)
    app.base_from.insert(0, "10")
    app.base_from.pack(side="left", padx=2)

    ttk.Label(conv_frame, text="To base").pack(side="left")
    app.base_to = tk.Entry(conv_frame, width=5)
    app.base_to.insert(0, "4")
    app.base_to.pack(side="left", padx=2)

    ttk.Button(conv_frame, text="Convert", command=lambda: convert_base(app)).pack(side="left", padx=6)
    app.base_result = ttk.Label(conv_frame, text="Result: ")
    app.base_result.pack(side="left", padx=6)


# -------------------------
# Helper functions
# -------------------------

def add_number(app):
    # Default new row
    app.numbers_tree.insert("", "end", values=("0", "NEW", "NEW", "∅"))


def delete_number(app):
    sel = app.numbers_tree.selection()
    for s in sel:
        app.numbers_tree.delete(s)


def save_numbers(app):
    if not app.current_language:
        messagebox.showwarning("No language", "Select a language first.")
        return
    langdir = ensure_language_dir(app.current_language)
    rows = []
    for iid in app.numbers_tree.get_children():
        val, word, pron, sym = app.numbers_tree.item(iid, "values")
        rows.append({
            "value": val,
            "word": word,
            "pronunciation": pron,
            "symbol": sym
        })
    save_csv(os.path.join(langdir, NUMBERS_FILE), ["value", "word", "pronunciation", "symbol"], rows)
    messagebox.showinfo("Saved", f"Numbers saved for {app.current_language}.")


def load_numbers(app, lang):
    if not lang:
        return
    langdir = ensure_language_dir(lang)
    path = os.path.join(langdir, NUMBERS_FILE)
    rows = load_csv(path, ["value", "word", "pronunciation", "symbol"])
    app.numbers_tree.delete(*app.numbers_tree.get_children())
    for r in rows:
        app.numbers_tree.insert("", "end", values=(
            r.get("value", ""),
            r.get("word", ""),
            r.get("pronunciation", ""),
            r.get("symbol", "")
        ))


def convert_base(app):
    try:
        num_str = app.base_input.get().strip()
        from_base = int(app.base_from.get())
        to_base = int(app.base_to.get())
        # Convert input to integer
        num = int(num_str, from_base)
        # Convert integer to target base string
        digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if num == 0:
            result = "0"
        else:
            result = ""
            n = num
            while n > 0:
                result = digits[n % to_base] + result
                n //= to_base
        app.base_result.config(text=f"Result: {result}")
    except Exception as e:
        messagebox.showerror("Error", f"Conversion failed: {e}")
