# widgets/compare_tab.py
import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from constants import FONTS_DIRNAME



from utils.file_io import load_csv
from constants import (
    DICT_FILE, DICT_FIELDS,
    PHONO_FILE, PHONO_FIELDS,
    GRAMMAR_TEXT,
    NUMBERS_FILE,
    LANG_ROOT
)

def build_compare_tab(app):
    """Attach the Compare tab to the main notebook with sub-tabs for each module."""
    tab = ttk.Frame(app.notebook)
    app.notebook.add(tab, text="Compare")

    subnb = ttk.Notebook(tab)
    subnb.pack(fill="both", expand=True, padx=6, pady=6)

    # Dictionary
    frame_dict = ttk.Frame(subnb); subnb.add(frame_dict, text="Dictionary")
    build_dict_compare(frame_dict)

    # Phonology
    frame_phono = ttk.Frame(subnb); subnb.add(frame_phono, text="Phonology")
    build_phono_compare(frame_phono)

    # Grammar
    frame_gram = ttk.Frame(subnb); subnb.add(frame_gram, text="Grammar")
    build_grammar_compare(frame_gram)

    # Numbers
    frame_num = ttk.Frame(subnb); subnb.add(frame_num, text="Numbers")
    build_numbers_compare(frame_num)

    # Fonts
    frame_fonts = ttk.Frame(subnb); subnb.add(frame_fonts, text="Fonts")
    build_fonts_compare(frame_fonts)

    # Translation
    frame_trans = ttk.Frame(subnb); subnb.add(frame_trans, text="Translation")
    build_translation_compare(frame_trans)


# -------------------------
# Utility: get available languages
# -------------------------
def get_languages():
    if not os.path.exists(LANG_ROOT):
        return []
    return [d for d in os.listdir(LANG_ROOT) if os.path.isdir(os.path.join(LANG_ROOT, d))]


# -------------------------
# Dictionary comparison
# -------------------------
def build_dict_compare(frame):
    top = ttk.Frame(frame); top.pack(fill="x", padx=6, pady=6)
    lang_a = ttk.Combobox(top, values=get_languages(), width=20); lang_a.pack(side="left", padx=4)
    lang_b = ttk.Combobox(top, values=get_languages(), width=20); lang_b.pack(side="left", padx=4)
    tree = ttk.Treeview(frame, columns=("english","lang_a","lang_b"), show="headings", height=20)
    for c in ("english","lang_a","lang_b"):
        tree.heading(c, text=c.capitalize()); tree.column(c, width=180)
    tree.pack(fill="both", expand=True, padx=6, pady=6)

    def compare():
        la, lb = lang_a.get(), lang_b.get()
        if not la or not lb or la == lb:
            messagebox.showwarning("Select", "Choose two different languages.")
            return
        dict_a = load_lang_dict(la)
        dict_b = load_lang_dict(lb)
        tree.delete(*tree.get_children())
        all_eng = sorted(set(dict_a.keys()) | set(dict_b.keys()))
        for eng in all_eng:
            tree.insert("", "end", values=(eng, dict_a.get(eng,""), dict_b.get(eng,"")))
    ttk.Button(top, text="Compare", command=compare).pack(side="left", padx=6)


def load_lang_dict(lang):
    path = os.path.join(LANG_ROOT, lang, DICT_FILE)
    rows = load_csv(path, DICT_FIELDS)
    d = {}
    for r in rows:
        eng = (r.get("english") or "").strip().lower()
        if eng:
            d[eng] = r.get("conlang","")
    return d


# -------------------------
# Phonology comparison
# -------------------------
def build_phono_compare(frame):
    top = ttk.Frame(frame); top.pack(fill="x", padx=6, pady=6)
    lang_a = ttk.Combobox(top, values=get_languages(), width=20); lang_a.pack(side="left", padx=4)
    lang_b = ttk.Combobox(top, values=get_languages(), width=20); lang_b.pack(side="left", padx=4)
    tree = ttk.Treeview(frame, columns=("ipa","a","b"), show="headings", height=20)
    for c in ("ipa","a","b"):
        tree.heading(c, text=c.upper()); tree.column(c, width=180)
    tree.pack(fill="both", expand=True, padx=6, pady=6)

    def compare():
        la, lb = lang_a.get(), lang_b.get()
        if not la or not lb or la == lb:
            messagebox.showwarning("Select", "Choose two different languages.")
            return
        rows_a = load_csv(os.path.join(LANG_ROOT, la, PHONO_FILE), PHONO_FIELDS)
        rows_b = load_csv(os.path.join(LANG_ROOT, lb, PHONO_FILE), PHONO_FIELDS)
        ipa_a = {r["ipa"]: r for r in rows_a if r.get("ipa")}
        ipa_b = {r["ipa"]: r for r in rows_b if r.get("ipa")}
        all_ipa = sorted(set(ipa_a.keys()) | set(ipa_b.keys()))
        tree.delete(*tree.get_children())
        for ipa in all_ipa:
            tree.insert("", "end", values=(ipa, "✓" if ipa in ipa_a else "", "✓" if ipa in ipa_b else ""))
    ttk.Button(top, text="Compare", command=compare).pack(side="left", padx=6)


# -------------------------
# Grammar comparison
# -------------------------
def build_grammar_compare(frame):
    top = ttk.Frame(frame); top.pack(fill="x", padx=6, pady=6)
    lang_a = ttk.Combobox(top, values=get_languages(), width=20); lang_a.pack(side="left", padx=4)
    lang_b = ttk.Combobox(top, values=get_languages(), width=20); lang_b.pack(side="left", padx=4)
    text = tk.Text(frame, wrap="word", height=25)
    text.pack(fill="both", expand=True, padx=6, pady=6)

    def compare():
        la, lb = lang_a.get(), lang_b.get()
        if not la or not lb or la == lb:
            messagebox.showwarning("Select", "Choose two different languages.")
            return
        path_a = os.path.join(LANG_ROOT, la, GRAMMAR_TEXT)
        path_b = os.path.join(LANG_ROOT, lb, GRAMMAR_TEXT)
        text.delete("1.0", tk.END)
        if os.path.exists(path_a):
            with open(path_a, encoding="utf-8") as f:
                text.insert(tk.END, f"--- {la} ---\n{f.read()}\n\n")
        if os.path.exists(path_b):
            with open(path_b, encoding="utf-8") as f:
                text.insert(tk.END, f"--- {lb} ---\n{f.read()}\n\n")
    ttk.Button(top, text="Compare", command=compare).pack(side="left", padx=6)


# -------------------------
# Numbers comparison
# -------------------------
def build_numbers_compare(frame):
    top = ttk.Frame(frame); top.pack(fill="x", padx=6, pady=6)
    lang_a = ttk.Combobox(top, values=get_languages(), width=20); lang_a.pack(side="left", padx=4)
    lang_b = ttk.Combobox(top, values=get_languages(), width=20); lang_b.pack(side="left", padx=4)
    tree = ttk.Treeview(frame, columns=("value","a","b"), show="headings", height=20)
    for c in ("value","a","b"):
        tree.heading(c, text=c.capitalize()); tree.column(c, width=180)
    tree.pack(fill="both", expand=True, padx=6, pady=6)

    def compare():
        la, lb = lang_a.get(), lang_b.get()
        if not la or not lb or la == lb:
            messagebox.showwarning("Select", "Choose two different languages.")
            return
        rows_a = load_csv(os.path.join(LANG_ROOT, la, NUMBERS_FILE), ["value","word"])
        rows_b = load_csv(os.path.join(LANG_ROOT, lb, NUMBERS_FILE), ["value","word"])
        dict_a = {r["value"]: r["word"] for r in rows_a if r.get("value")}
        dict_b = {r["value"]: r["word"] for r in rows_b if r.get("value")}
        all_vals = sorted(set(dict_a.keys()) | set(dict_b.keys()), key=lambda x: int(x) if x.isdigit() else x)
        tree.delete(*tree.get_children())
        for v in all_vals:
            tree.insert("", "end", values=(v, dict_a.get(v,""), dict_b.get(v,"")))
    ttk.Button(top, text="Compare", command=compare).pack(side="left", padx=6)


from PIL import Image, ImageTk
from constants import FONTS_DIRNAME

def build_fonts_compare(frame):
    top = ttk.Frame(frame); top.pack(fill="x", padx=6, pady=6)
    ttk.Label(top, text="Language A:").pack(side="left")
    lang_a = ttk.Combobox(top, values=get_languages(), width=20); lang_a.pack(side="left", padx=4)
    font_a = ttk.Combobox(top, values=[], width=20); font_a.pack(side="left", padx=4)

    ttk.Label(top, text="Language B:").pack(side="left")
    lang_b = ttk.Combobox(top, values=get_languages(), width=20); lang_b.pack(side="left", padx=4)
    font_b = ttk.Combobox(top, values=[], width=20); font_b.pack(side="left", padx=4)

    # Use a Canvas for side-by-side thumbnails
    canvas = tk.Canvas(frame, bg="white")
    canvas.pack(fill="both", expand=True, padx=6, pady=6)

    thumbnails = {}

    def populate_fonts(event=None):
        combo = event.widget
        lang = combo.get()
        if not lang: return
        fonts_dir = os.path.join(LANG_ROOT, lang, FONTS_DIRNAME)
        fonts = [d for d in os.listdir(fonts_dir) if os.path.isdir(os.path.join(fonts_dir, d))] if os.path.exists(fonts_dir) else []
        if combo == lang_a:
            font_a["values"] = fonts
        elif combo == lang_b:
            font_b["values"] = fonts

    lang_a.bind("<<ComboboxSelected>>", populate_fonts)
    lang_b.bind("<<ComboboxSelected>>", populate_fonts)

    def compare():
        la, lb = lang_a.get(), lang_b.get()
        fa, fb = font_a.get(), font_b.get()
        if not la or not lb or la == lb:
            messagebox.showwarning("Select", "Choose two different languages.")
            return
        if not fa or not fb:
            messagebox.showwarning("Select", "Choose fonts for both languages.")
            return

        map_a = load_font_mapping(la, fa)
        map_b = load_font_mapping(lb, fb)
        all_syms = sorted(set(map_a.keys()) | set(map_b.keys()))

        canvas.delete("all")
        thumbnails.clear()

        y = 10
        for sym in all_syms:
            img_a = make_thumbnail(os.path.join(LANG_ROOT, la, FONTS_DIRNAME, fa, map_a.get(sym,"")))
            img_b = make_thumbnail(os.path.join(LANG_ROOT, lb, FONTS_DIRNAME, fb, map_b.get(sym,"")))
            if img_a: thumbnails[f"{sym}_a"] = img_a
            if img_b: thumbnails[f"{sym}_b"] = img_b

            # Draw symbol label
            canvas.create_text(10, y+16, text=sym, anchor="w", font=("Segoe UI", 10, "bold"))

            # Draw Lang A thumbnail
            if img_a:
                canvas.create_image(120, y+16, image=img_a, anchor="center")
            else:
                canvas.create_text(120, y+16, text="—", anchor="center")

            # Draw Lang B thumbnail
            if img_b:
                canvas.create_image(200, y+16, image=img_b, anchor="center")
            else:
                canvas.create_text(200, y+16, text="—", anchor="center")

            y += 40

    ttk.Button(top, text="Compare", command=compare).pack(side="left", padx=6)


def load_font_mapping(lang, font):
    folder = os.path.join(LANG_ROOT, lang, FONTS_DIRNAME, font)
    mapping_file = os.path.join(folder, "mapping.csv")
    if not os.path.exists(mapping_file):
        return {}
    rows = load_csv(mapping_file, ["symbol","filename"])
    return {r["symbol"]: r["filename"] for r in rows if r.get("symbol")}


def make_thumbnail(path):
    if not path or not os.path.exists(path):
        return None
    try:
        img = Image.open(path)
        img.thumbnail((32,32))
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


def build_translation_compare(frame):
    top = ttk.Frame(frame); top.pack(fill="x", padx=6, pady=6)

    ttk.Label(top, text="Language A:").pack(side="left")
    lang_a = ttk.Combobox(top, values=get_languages(), width=20); lang_a.pack(side="left", padx=4)

    ttk.Label(top, text="Language B:").pack(side="left")
    lang_b = ttk.Combobox(top, values=get_languages(), width=20); lang_b.pack(side="left", padx=4)

    ttk.Label(top, text="English Input:").pack(side="left", padx=(12,0))
    input_entry = tk.Entry(top, width=40); input_entry.pack(side="left", padx=4)

    ttk.Button(top, text="Compare Translation",
               command=lambda: compare()).pack(side="left", padx=6)

    # Output text areas
    out_frame = ttk.Frame(frame); out_frame.pack(fill="both", expand=True, padx=6, pady=6)
    text_a = tk.Text(out_frame, height=8, wrap="word",
                     bg="#1b1b1b", fg="#eaeaea", insertbackground="white")
    text_b = tk.Text(out_frame, height=8, wrap="word",
                     bg="#1b1b1b", fg="#eaeaea", insertbackground="white")
    text_a.pack(side="left", fill="both", expand=True, padx=4)
    text_b.pack(side="left", fill="both", expand=True, padx=4)

    def compare():
        la, lb = lang_a.get(), lang_b.get()
        phrase = input_entry.get().strip().lower()
        if not la or not lb or la == lb:
            messagebox.showwarning("Select", "Choose two different languages.")
            return
        if not phrase:
            return

        # Load dictionaries
        dict_a = load_lang_dict(la)
        dict_b = load_lang_dict(lb)

        # Translate word by word
        def translate(phrase, d):
            words = phrase.split()
            out = []
            for w in words:
                out.append(d.get(w, f"[{w}]"))
            return " ".join(out)

        trans_a = translate(phrase, dict_a)
        trans_b = translate(phrase, dict_b)

        text_a.delete("1.0", tk.END); text_a.insert(tk.END, f"{la}:\n{trans_a}")
        text_b.delete("1.0", tk.END); text_b.insert(tk.END, f"{lb}:\n{trans_b}")
