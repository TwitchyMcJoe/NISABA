# widgets/import_export_tab.py
import os
import shutil
import zipfile
from tkinter import ttk, simpledialog, messagebox, filedialog

from utils.file_io import ensure_language_dir, get_languages
from constants import LANG_ROOT


def build_import_export_tab(app):
    """Attach the Import/Export tab to the main notebook."""
    tab = ttk.Frame(app.notebook)
    app.notebook.add(tab, text="Import / Export")

    frame = ttk.Frame(tab)
    frame.pack(fill="x", padx=8, pady=8)
    ttk.Label(frame, text="Languages:").pack(side="left", padx=(0, 8))
    app.lang_combo = ttk.Combobox(frame, values=get_languages(), width=30)
    app.lang_combo.set("Select Language")
    app.lang_combo.pack(side="left", padx=4)
    ttk.Button(frame, text="Load Language", command=app.load_selected_language).pack(side="left", padx=4)
    ttk.Button(frame, text="New Language", command=app.create_new_language).pack(side="left", padx=4)
    ttk.Button(frame, text="Delete Language", command=app.delete_language).pack(side="left", padx=4)

    zf = ttk.Frame(tab)
    zf.pack(fill="x", padx=8, pady=10)
    ttk.Button(zf, text="Export Language (.zip)", command=app.export_language_zip).pack(side="left", padx=6)
    ttk.Button(zf, text="Import Language (.zip)", command=app.import_language_zip).pack(side="left", padx=6)

    app.import_status = ttk.Label(tab, text="", foreground="lightgreen")
    app.import_status.pack(anchor="w", padx=8)


# -------------------------
# Methods bound to ConlangApp
# -------------------------

def load_selected_language(self):
    lang = self.lang_combo.get()
    if not lang or lang == "Select Language":
        messagebox.showwarning("Select", "Choose a language from the dropdown.")
        return
    self.load_language(lang)

def create_new_language(self):
    name = simpledialog.askstring("New Language", "Language name:")
    if not name:
        return
    ensure_language_dir(name)
    self.refresh_language_list()
    self.lang_combo.set(name)
    self.load_language(name)

def delete_language(self):
    lang = self.lang_combo.get()
    if not lang or lang == "Select Language":
        messagebox.showwarning("Select", "Choose a language.")
        return
    if messagebox.askyesno("Delete", f"Delete language {lang}? This will remove its folder."):
        shutil.rmtree(os.path.join(LANG_ROOT, lang))
        self.refresh_language_list()
        self.lang_combo.set("Select Language")
        messagebox.showinfo("Deleted", f"{lang} removed.")

def export_language_zip(self):
    lang = self.lang_combo.get()
    if not lang or lang == "Select Language":
        messagebox.showwarning("Select", "Choose a language.")
        return
    dest = filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("Zip","*.zip")])
    if not dest:
        return
    srcdir = os.path.join(LANG_ROOT, lang)
    with zipfile.ZipFile(dest, "w") as z:
        for root, dirs, files in os.walk(srcdir):
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, start=LANG_ROOT)
                z.write(full, rel)
    messagebox.showinfo("Exported", f"Exported {lang} to {dest}")

def import_language_zip(self):
    path = filedialog.askopenfilename(filetypes=[("Zip files","*.zip")])
    if not path:
        return
    with zipfile.ZipFile(path, "r") as z:
        z.extractall(LANG_ROOT)
    self.refresh_language_list()
    messagebox.showinfo("Imported", f"Imported language archive: {path}")
