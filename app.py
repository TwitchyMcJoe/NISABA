# app.py
import tkinter as tk
from tkinter import ttk, messagebox

# Core
from constants import LANG_ROOT
from utils.file_io import get_languages
# Tabs
from widgets import import_export_tab, phonology_tab, fonts_tab, dictionary_tab
from widgets import grammar_tab, numbers_tab, compare_tab, translation_tab


class ConlangApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Conlang Assistant")
        self.geometry("1200x820")
        self.configure(bg="#2b2b2b")

        # style
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure("TLabel", background="#2b2b2b", foreground="white")
        self.style.configure("TFrame", background="#2b2b2b")
        self.style.configure("TButton", background="#4b4b4b", foreground="white")
        self.style.map("TButton", background=[("active", "#666666")])
        self.style.configure("Treeview",
                             background="#1e1e1e",
                             fieldbackground="#1e1e1e",
                             foreground="white")

        # runtime state
        self.current_language = None
        self.dictionary = {}
        self.conjugations = []
        self.phonology = []
        self.phonotactics = ""
        self.current_font = None
        self.font_preview_mapping = []

        # Bind methods from tab modules
        self.load_selected_language = import_export_tab.load_selected_language.__get__(self)
        self.create_new_language = import_export_tab.create_new_language.__get__(self)
        self.delete_language = import_export_tab.delete_language.__get__(self)
        self.export_language_zip = import_export_tab.export_language_zip.__get__(self)
        self.import_language_zip = import_export_tab.import_language_zip.__get__(self)

        self.load_phonology_files = phonology_tab.load_phonology_files.__get__(self)
        self.load_dictionary = dictionary_tab.load_dictionary.__get__(self)
        self.update_dict_table = dictionary_tab.update_dict_table.__get__(self)
        self.save_dictionary = dictionary_tab.save_dictionary.__get__(self)

        self.load_numbers = numbers_tab.load_numbers.__get__(self)

        # build UI
        self.create_widgets()
        self.refresh_language_list()


    def create_widgets(self):
        ttk.Label(self, text="Conlang Assistant",
                  font=("Segoe UI", 18, "bold")).pack(pady=8)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        # Tabs
        import_export_tab.build_import_export_tab(self)
        phonology_tab.build_phonology_tab(self)
        dictionary_tab.build_dictionary_tab(self)
        grammar_tab.build_grammar_tab(self)
        numbers_tab.build_numbers_tab(self)
        fonts_tab.build_fonts_tab(self)
        compare_tab.build_compare_tab(self)
        translation_tab.build_translation_tab(self)

        ttk.Button(self, text="Exit", command=self.on_exit).pack(pady=6)

    def refresh_language_list(self):
        langs = get_languages()
        try:
            self.lang_combo["values"] = langs
            self.font_lang_combo["values"] = langs
            self.compare_lang_a["values"] = langs
            self.compare_lang_b["values"] = langs
        except Exception:
            pass

    def load_language(self, lang):
        """Called when a language is selected/created."""
        self.current_language = lang
        self.title(f"Conlang Assistant - {lang}")
        # Load dictionary, phonology, numbers, grammar
        self.load_dictionary(lang)
        self.load_phonology_files(lang)
        self.load_numbers(lang)
        
    def enable_incell_editing(self, tree):
        def on_double_click(event):
            region = tree.identify("region", event.x, event.y)
            if region != "cell":
                return
            rowid = tree.identify_row(event.y)
            colid = tree.identify_column(event.x)
            if not rowid or not colid:
                return

            bbox = tree.bbox(rowid, colid)
            if not bbox:
                return
            x, y, width, height = bbox
            col_index = int(colid.replace("#", "")) - 1
            col_name = tree["columns"][col_index]
            old_value = tree.item(rowid, "values")[col_index]

            entry = tk.Entry(tree)
            entry.place(x=x, y=y, width=width, height=height)
            entry.insert(0, old_value)
            entry.focus()

            def save_edit(event=None):
                new_val = entry.get()
                vals = list(tree.item(rowid, "values"))
                vals[col_index] = new_val
                tree.item(rowid, values=vals)
                entry.destroy()
                # 🔑 auto-save grammar after any edit
                try:
                    from widgets import grammar_tab
                    grammar_tab.save_grammar(self)
                except Exception as e:
                    print("Auto-save failed:", e)

            def cancel_edit(event=None):
                entry.destroy()

            entry.bind("<Return>", save_edit)
            entry.bind("<FocusOut>", save_edit)
            entry.bind("<Escape>", cancel_edit)

        tree.bind("<Double-1>", on_double_click)



    def on_exit(self):
        if messagebox.askyesno("Exit", "Are you sure you want to quit?"):
            self.destroy()
