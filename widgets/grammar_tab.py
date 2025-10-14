import os
import tkinter as tk
from tkinter import ttk, messagebox

from constants import LANG_ROOT, GRAMMAR_TEXT, CONJ_FILE, CONJ_FIELDS
from utils.file_io import ensure_language_dir, save_csv, load_csv


def build_grammar_tab(app):
    tab = ttk.Frame(app.notebook)
    app.notebook.add(tab, text="Grammar")

    top = ttk.Frame(tab); top.pack(fill="x", padx=6, pady=6)
    ttk.Button(top, text="Reload Grammar", command=lambda: reload_grammar(app)).pack(side="left", padx=4)
    ttk.Button(top, text="Save Grammar", command=lambda: save_grammar(app)).pack(side="left", padx=4)

    subnb = ttk.Notebook(tab); subnb.pack(fill="both", expand=True, padx=6, pady=6)

    # Summary (auto-generated, read-only)
    frame_summary = ttk.Frame(subnb)
    subnb.add(frame_summary, text="Summary")
    app.grammar_summary = tk.Text(
        frame_summary, height=12, bg="#1b1b1b", fg="#eaeaea",
        insertbackground="white", wrap="word"
    )
    app.grammar_summary.pack(fill="both", expand=True, padx=6, pady=6)
    app.grammar_summary.config(state="disabled")  # read-only


    # Prefixes
    app.prefix_tree = make_table(subnb, "Prefixes", ("POS","Prefixes"), app)

    # Suffixes
    app.suffix_tree = make_table(subnb, "Suffixes", ("POS","Suffixes"), app)

    # Nouns
    app.noun_tree = make_table(subnb, "Nouns", ("Category","Prefix","Suffix","Notes"), app)

    # Articles
    app.articles_tree = make_table(subnb, "Articles", ("Type","Form","Notes"), app)

    # Pronouns
    app.pron_tree = make_table(subnb, "Pronouns", ("Person","Case","Form","Notes"), app)

    # Possession
    app.poss_tree = make_table(subnb, "Possession", ("Owner","Marker","Notes"), app)

    # Verbs
    app.verbs_tree = make_table(subnb, "Verbs", ("Base","Class","Notes"), app)

    # Conjugations
    app.conj_tree = make_table(subnb, "Conjugations", CONJ_FIELDS, app)

    # Transforms
    frame_trans = ttk.Frame(subnb); subnb.add(frame_trans, text="Transforms")
    app.transforms_editor = tk.Text(frame_trans, height=8, bg="#1b1b1b", fg="#eaeaea", insertbackground="white")
    app.transforms_editor.pack(fill="both", expand=True, padx=6, pady=6)

    # Notes (user editable)
    frame_notes = ttk.Frame(subnb)
    subnb.add(frame_notes, text="Notes")
    app.grammar_notes = tk.Text(
        frame_notes, height=10, bg="#1b1b1b", fg="#eaeaea", insertbackground="white"
    )
    app.grammar_notes.pack(fill="both", expand=True, padx=6, pady=6)



def make_table(subnb, label, cols, app):
    frame = ttk.Frame(subnb); subnb.add(frame, text=label)
    tree = ttk.Treeview(frame, columns=cols, show="headings", height=10)
    for c in cols: tree.heading(c, text=c)
    tree.pack(fill="both", expand=True, padx=6, pady=6)
    app.enable_incell_editing(tree)
    ttk.Button(frame, text="Add", command=lambda: add_row(tree,len(cols))).pack(padx=4,pady=2)
    return tree


def add_row(tree, ncols):
    values = ["new"] + ["" for _ in range(ncols-1)]
    tree.insert("", "end", values=tuple(values))


def save_grammar(app):
    if not app.current_language:
        messagebox.showwarning("No language", "Select a language first.")
        return
    langdir = ensure_language_dir(app.current_language)
    path = os.path.join(langdir, GRAMMAR_TEXT)

    with open(path, "w", encoding="utf-8") as f:
        # Save user notes
        f.write("[NOTES]\n" + app.grammar_notes.get("1.0", tk.END).strip() + "\n\n")

        # Save each rule table
        dump_tree(app.prefix_tree, "PREFIXES", f)
        dump_tree(app.suffix_tree, "SUFFIXES", f)
        dump_tree(app.noun_tree, "NOUNS", f)
        dump_tree(app.articles_tree, "ARTICLES", f)
        dump_tree(app.pron_tree, "PRONOUNS", f)
        dump_tree(app.poss_tree, "POSSESSION", f)
        dump_tree(app.verbs_tree, "VERBS", f)
        dump_tree(app.conj_tree, "CONJUGATIONS", f)

        # Save transforms
        f.write("[TRANSFORMS]\n" + app.transforms_editor.get("1.0", tk.END).strip() + "\n")

    # Save conjugations separately as CSV
    rows = []
    for iid in app.conj_tree.get_children():
        vals = app.conj_tree.item(iid, "values")
        rows.append({c: vals[i] for i, c in enumerate(CONJ_FIELDS)})
    save_csv(os.path.join(langdir, CONJ_FILE), CONJ_FIELDS, rows)

    # Refresh summary after saving
    update_summary(app)

    messagebox.showinfo("Saved", f"Grammar saved for {app.current_language}")



def dump_tree(tree, header, f):
    cols = tree["columns"]
    f.write(f"[{header}]\n")
    f.write(",".join(cols)+"\n")
    for iid in tree.get_children():
        vals = tree.item(iid,"values")
        f.write(",".join(vals)+"\n")
    f.write("\n")


def reload_grammar(app):
    if not app.current_language:
        return
    langdir = os.path.join(LANG_ROOT, app.current_language)
    path = os.path.join(langdir, GRAMMAR_TEXT)
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    section = None

    # Clear editors and tables
    app.grammar_notes.delete("1.0", tk.END)
    app.transforms_editor.delete("1.0", tk.END)
    for t in (app.prefix_tree, app.suffix_tree, app.noun_tree,
              app.articles_tree, app.pron_tree, app.poss_tree,
              app.verbs_tree, app.conj_tree):
        t.delete(*t.get_children())

    # Parse file
    for ln in lines:
        if not ln:
            continue
        if ln.startswith("[") and ln.endswith("]"):
            section = ln.strip("[]").upper()
            continue
        if section == "NOTES":
            app.grammar_notes.insert(tk.END, ln + "\n")
        elif section == "TRANSFORMS":
            app.transforms_editor.insert(tk.END, ln + "\n")
        elif section in ("PREFIXES", "SUFFIXES", "NOUNS", "ARTICLES",
                         "PRONOUNS", "POSSESSION", "VERBS", "CONJUGATIONS"):
            if "," in ln and not ln.lower().startswith(
                ("pos", "category", "type", "person", "owner", "base", "english")
            ):
                vals = ln.split(",")
                target = {
                    "PREFIXES": app.prefix_tree,
                    "SUFFIXES": app.suffix_tree,
                    "NOUNS": app.noun_tree,
                    "ARTICLES": app.articles_tree,
                    "PRONOUNS": app.pron_tree,
                    "POSSESSION": app.poss_tree,
                    "VERBS": app.verbs_tree,
                    "CONJUGATIONS": app.conj_tree,
                }[section]
                target.insert("", "end", values=vals)

    # Refresh summary after reload
    update_summary(app)


def update_summary(app):
    app.grammar_summary.config(state="normal")
    app.grammar_summary.delete("1.0", tk.END)
    app.grammar_summary.tag_configure("header", foreground="#FFD700", font=("TkDefaultFont", 10, "bold"))
    app.grammar_summary.tag_configure("prefix", foreground="#00CED1")
    app.grammar_summary.tag_configure("suffix", foreground="#FF69B4")
    app.grammar_summary.tag_configure("noun", foreground="#ADFF2F")
    app.grammar_summary.tag_configure("article", foreground="#FFA500")
    app.grammar_summary.tag_configure("pronoun", foreground="#87CEFA")
    app.grammar_summary.tag_configure("poss", foreground="#DA70D6")
    app.grammar_summary.tag_configure("verb", foreground="#FF6347")
    app.grammar_summary.tag_configure("conj", foreground="#7FFFD4")
    app.grammar_summary.tag_configure("transform", foreground="#C0C0C0", font=("TkDefaultFont", 9, "italic"))


    def add_section(title, tree, color):
        app.grammar_summary.insert(tk.END, f"{title}\n", ("header",))
        for iid in tree.get_children():
            vals = tree.item(iid, "values")
            line = " • " + " | ".join(vals) + "\n"
            app.grammar_summary.insert(tk.END, line, (color,))
        app.grammar_summary.insert(tk.END, "\n")

    # Rule tables
    add_section("Prefixes", app.prefix_tree, "prefix")
    add_section("Suffixes", app.suffix_tree, "suffix")
    add_section("Nouns", app.noun_tree, "noun")
    add_section("Articles", app.articles_tree, "article")
    add_section("Pronouns", app.pron_tree, "pronoun")
    add_section("Possession", app.poss_tree, "poss")
    add_section("Verbs", app.verbs_tree, "verb")
    add_section("Conjugations", app.conj_tree, "conj")

    # Transforms section
    app.grammar_summary.insert(tk.END, "Transforms\n", ("header",))
    transforms_text = app.transforms_editor.get("1.0", tk.END).strip()
    if transforms_text:
        for line in transforms_text.splitlines():
            app.grammar_summary.insert(tk.END, " ↳ " + line + "\n", ("transform",))
    else:
        app.grammar_summary.insert(tk.END, "(none)\n", ("transform",))
    app.grammar_summary.insert(tk.END, "\n")

    app.grammar_summary.config(state="disabled")
