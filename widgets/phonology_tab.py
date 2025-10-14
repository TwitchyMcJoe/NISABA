# widgets/phonology_tab.py
import os
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox

from utils.file_io import load_csv, save_csv, ensure_language_dir
from constants import LANG_ROOT, PHONO_FILE, PHONO_FIELDS, PHONOTEXT



def build_phonology_tab(app):
    """Attach the Phonology & Spelling tab to the main notebook."""
    tab = ttk.Frame(app.notebook)
    app.notebook.add(tab, text="Phonology & Spelling")

    ttk.Label(tab, text="Phonology & Spelling",
              font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=10, pady=(8, 4))

    sub_nb = ttk.Notebook(tab)
    sub_nb.pack(fill="both", expand=True, padx=8, pady=8)

    # Consonants
    frame_cons = ttk.Frame(sub_nb)
    sub_nb.add(frame_cons, text="Consonants")
    app.phono_cons_tree = ttk.Treeview(frame_cons,
                                       columns=("ipa", "example", "type", "notes"),
                                       show="headings", height=12)
    for col, w in (("ipa", 80), ("example", 180), ("type", 140), ("notes", 380)):
        app.phono_cons_tree.heading(col, text=col.capitalize())
        app.phono_cons_tree.column(col, width=w)
    app.phono_cons_tree.pack(fill="both", expand=True, padx=6, pady=6)
    # After app.phono_cons_tree.pack(...), app.phono_vow_tree.pack(...)
    from utils.table_edit import enable_treeview_editing
    enable_treeview_editing(app.phono_cons_tree)
    attach_type_dropdown(app.phono_cons_tree)

    cons_ctrl = ttk.Frame(frame_cons); cons_ctrl.pack(fill="x", padx=6, pady=6)
    ttk.Button(cons_ctrl, text="Add", command=lambda: add_phoneme(app, app.phono_cons_tree)).pack(side="left", padx=4)
    ttk.Button(cons_ctrl, text="Delete", command=lambda: delete_phoneme(app, app.phono_cons_tree)).pack(side="left", padx=4)
    ttk.Button(cons_ctrl, text="Save", command=lambda: save_phonology_files(app)).pack(side="left", padx=4)

    # Vowels
    frame_vow = ttk.Frame(sub_nb)
    sub_nb.add(frame_vow, text="Vowels")
    app.phono_vow_tree = ttk.Treeview(frame_vow,
                                      columns=("ipa", "example", "type", "notes"),
                                      show="headings", height=8)
    for col, w in (("ipa", 80), ("example", 180), ("type", 140), ("notes", 380)):
        app.phono_vow_tree.heading(col, text=col.capitalize())
        app.phono_vow_tree.column(col, width=w)
    app.phono_vow_tree.pack(fill="both", expand=True, padx=6, pady=6)
    # After app.phono_cons_tree.pack(...), app.phono_vow_tree.pack(...)
    from utils.table_edit import enable_treeview_editing
    enable_treeview_editing(app.phono_vow_tree)
    attach_type_dropdown(app.phono_vow_tree)

    vow_ctrl = ttk.Frame(frame_vow); vow_ctrl.pack(fill="x", padx=6, pady=6)
    ttk.Button(vow_ctrl, text="Add", command=lambda: add_phoneme(app, app.phono_vow_tree)).pack(side="left", padx=4)
    ttk.Button(vow_ctrl, text="Delete", command=lambda: delete_phoneme(app, app.phono_vow_tree)).pack(side="left", padx=4)
    ttk.Button(vow_ctrl, text="Save", command=lambda: save_phonology_files(app)).pack(side="left", padx=4)

    # Syllable
    frame_syl = ttk.Frame(sub_nb)
    sub_nb.add(frame_syl, text="Syllable Structure")
    ttk.Label(frame_syl, text="Syllable structure and constraints",
              font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=6, pady=(6, 2))
    app.syllable_text = tk.Text(frame_syl, height=8,
                                bg="#1b1b1b", fg="#eaeaea", insertbackground="white")
    app.syllable_text.pack(fill="both", expand=True, padx=6, pady=6)
    ttk.Button(frame_syl, text="Save", command=lambda: save_phonology_files(app)).pack(padx=6, pady=4)

    # Spelling
    frame_spell = ttk.Frame(sub_nb)
    sub_nb.add(frame_spell, text="Spelling Rules")
    ttk.Label(frame_spell, text="Spelling rules (pronunciation -> orthography)",
              font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=6, pady=(6, 2))
    app.spelling_text = tk.Text(frame_spell, height=10,
                                bg="#1b1b1b", fg="#eaeaea", insertbackground="white")
    app.spelling_text.pack(fill="both", expand=True, padx=6, pady=6)
    ttk.Button(frame_spell, text="Save", command=lambda: save_phonology_files(app)).pack(padx=6, pady=4)


# -------------------------
# Helper functions
# -------------------------

def add_phoneme(app, tree):
##    ipa = simpledialog.askstring("IPA", "IPA Symbol:")
##    if not ipa:
##        return
##    ex = simpledialog.askstring("Example", "Romanization / example:")
##    typ = simpledialog.askstring("Type", "Type (vowel, consonant, etc.):")
##    notes = simpledialog.askstring("Notes", "Notes:")
##    tree.insert("", "end", values=(ipa, ex or "", typ or "", notes or ""))
    tree.insert("", "end", values=("", "", "", "NEW"))


def add_consonant(app):
    app.phono_cons_tree.insert("", "end", values=("", "", "", ""))

def add_vowel(app):
    app.phono_vow_tree.insert("", "end", values=("", "", "", ""))


def delete_phoneme(app, tree):
    sel = tree.selection()
    for s in sel:
        tree.delete(s)

def save_phonology_files(app):
    if not app.current_language:
        messagebox.showwarning("No language", "Select or create a language in Import/Export first.")
        return
    langdir = ensure_language_dir(app.current_language)
    rows = []
    for tree in (app.phono_cons_tree, app.phono_vow_tree):
        for iid in tree.get_children():
            vals = tree.item(iid, "values")
            rows.append({"ipa": vals[0], "example": vals[1], "type": vals[2], "notes": vals[3]})
    save_csv(os.path.join(langdir, PHONO_FILE), PHONO_FIELDS, rows)
    with open(os.path.join(langdir, PHONOTEXT), "w", encoding="utf-8") as f:
        f.write(app.syllable_text.get("1.0", tk.END))
    with open(os.path.join(langdir, "spelling_rules.txt"), "w", encoding="utf-8") as f:
        f.write(app.spelling_text.get("1.0", tk.END))
    messagebox.showinfo("Saved", f"Phonology & spelling saved for {app.current_language}.")

def load_phonology_files(app, lang):
    langdir = os.path.join(LANG_ROOT, lang)
    rows = load_csv(os.path.join(langdir, PHONO_FILE), PHONO_FIELDS)
    app.phono_cons_tree.delete(*app.phono_cons_tree.get_children())
    app.phono_vow_tree.delete(*app.phono_vow_tree.get_children())
    for r in rows:
        typ = (r.get("type") or "").lower()
        if "vowel" in typ or "diph" in typ:
            app.phono_vow_tree.insert("", "end", values=(r.get("ipa",""), r.get("example",""),
                                                         r.get("type",""), r.get("notes","")))
        else:
            app.phono_cons_tree.insert("", "end", values=(r.get("ipa",""), r.get("example",""),
                                                          r.get("type",""), r.get("notes","")))
    ptxt = os.path.join(langdir, PHONOTEXT)
    if os.path.exists(ptxt):
        with open(ptxt, "r", encoding="utf-8") as f:
            app.syllable_text.delete("1.0", tk.END)
            app.syllable_text.insert(tk.END, f.read())
    spath = os.path.join(langdir, "spelling_rules.txt")
    if os.path.exists(spath):
        with open(spath, "r", encoding="utf-8") as f:
            app.spelling_text.delete("1.0", tk.END)
            app.spelling_text.insert(tk.END, f.read())

from tkinter import ttk

def attach_type_dropdown(tree):
    def begin_edit_type(event):
        region = tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        item = tree.identify_row(event.y)
        column = tree.identify_column(event.x)
        if not item or not column:
            return
        col_index = int(column.replace("#", "")) - 1
        col_name = tree["columns"][col_index]
        if col_name != "type":
            return  # let normal editing handle it

        bbox = tree.bbox(item, column)
        if not bbox:
            return
        x, y, w, h = bbox
        current_vals = tree.item(item, "values")
        current = current_vals[col_index] if col_index < len(current_vals) else ""

        combo = ttk.Combobox(tree, values=["consonant", "vowel", "diphthong"])
        combo.set(current)
        combo.place(x=x+1, y=y+1, width=w-2, height=h-2)
        combo.focus()

        def finish(event=None):
            newval = combo.get()
            vals = list(tree.item(item, "values"))
            vals[col_index] = newval
            tree.item(item, values=vals)
            combo.destroy()

        combo.bind("<Return>", finish)
        combo.bind("<FocusOut>", finish)

    tree.bind("<Double-1>", begin_edit_type, add="+")
