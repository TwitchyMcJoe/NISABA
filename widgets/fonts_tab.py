import os
import shutil
from tkinter import ttk, simpledialog, messagebox, filedialog
from PIL import Image, ImageTk

from utils.file_io import load_csv, save_csv
from constants import LANG_ROOT, FONTS_DIRNAME
from utils.font_export import export_font_ttf
from utils.fonttools_bitmap_export import export_font_ttf_bitmap

def build_fonts_tab(app):
    """Attach the Fonts tab to the main notebook."""
    tab = ttk.Frame(app.notebook)
    app.notebook.add(tab, text="Fonts")

    top = ttk.Frame(tab); top.pack(fill="x", padx=6, pady=6)
    ttk.Label(top, text="Font language:").pack(side="left")
    app.font_lang_combo = ttk.Combobox(top, values=[], width=24)
    app.font_lang_combo.set("Select Language")
    app.font_lang_combo.pack(side="left", padx=6)
    app.font_lang_combo.bind("<<ComboboxSelected>>", lambda e: populate_font_scripts(app))
    #ttk.Button(top, text="Load Fonts for Language", command=lambda: load_fonts_for_language(app)).pack(side="left", padx=6)
    ttk.Label(top, text="Script/Font:").pack(side="left", padx=(12,0))
    app.font_script_combo = ttk.Combobox(top, values=[], width=24)
    app.font_script_combo.bind("<<ComboboxSelected>>", lambda e: load_fonts_for_language(app))
    app.font_script_combo.set("Select Font")
    app.font_script_combo.pack(side="left", padx=6)
    ttk.Button(top, text="New Font Mapping", command=lambda: create_new_font_mapping(app)).pack(side="left", padx=6)

    # Treeview with thumbnails in the #0 column
    app.fonts_list = ttk.Treeview(tab, columns=("filename",), show="tree headings", height=12)
    app.fonts_list.heading("#0", text="Symbol")
    app.fonts_list.heading("filename", text="Image file")
    app.fonts_list.column("#0", width=160)
    app.fonts_list.column("filename", width=420)
    app.fonts_list.pack(fill="both", expand=True, padx=6, pady=6)

    from utils.table_edit import enable_treeview_editing
    enable_treeview_editing(app.fonts_list, save_callback=save_current_font_mapping, app=app)

    # Bind selection to preview
    app.fonts_list.bind("<<TreeviewSelect>>", lambda e: show_font_preview(app))

    ops = ttk.Frame(tab); ops.pack(fill="x", padx=6, pady=6)
    ttk.Button(ops, text="Add Symbol", command=lambda: add_font_symbol(app)).pack(side="left", padx=4)
    ttk.Button(ops, text="Replace Image", command=lambda: replace_font_image(app)).pack(side="left", padx=4)
    ttk.Button(ops, text="Delete Symbol", command=lambda: delete_font_symbol(app)).pack(side="left", padx=4)
    ttk.Button(ops, text="Save Mapping", command=lambda: save_current_font_mapping(app)).pack(side="left", padx=4)
    #ttk.Button(ops, text="Export to TTF", command=lambda: export_font_ttf(app)).pack(side="left", padx=4)
    ttk.Button(ops, text="Export to TTF (bitmap)", command=lambda: export_font_ttf_bitmap(app)).pack(side="left", padx=4)
    preview = ttk.Frame(tab); preview.pack(fill="x", padx=6, pady=6)
    ttk.Label(preview, text="Preview:").pack(side="left")
    app.font_preview_label = ttk.Label(preview)
    app.font_preview_label.pack(side="left", padx=6)

    # storage for thumbnails
    app.font_thumbnails = {}
    app.current_font = None


# -------------------------
# Helper functions
# -------------------------

def create_new_font_mapping(app):
    lang = app.font_lang_combo.get()
    if not lang or lang == "Select Language":
        messagebox.showwarning("Select", "Choose a language first.")
        return
    langdir = os.path.join(LANG_ROOT, lang)
    fonts_dir = os.path.join(langdir, FONTS_DIRNAME)
    os.makedirs(fonts_dir, exist_ok=True)

    fontname = simpledialog.askstring("New Font", "Enter a new font folder name:")
    if not fontname:
        return
    folder = os.path.join(fonts_dir, fontname)
    if os.path.exists(folder):
        messagebox.showerror("Exists", f"Font folder '{fontname}' already exists.")
        return
    os.makedirs(folder, exist_ok=True)

    mapping_file = os.path.join(folder, "mapping.csv")
    save_csv(mapping_file, ["symbol","filename"], [])

    app.fonts_list.delete(*app.fonts_list.get_children())
    app.current_font = (lang, fontname, folder)
    app.font_thumbnails = {}
    messagebox.showinfo("Created", f"New font mapping '{fontname}' created for {lang}. Now add symbols.")


def load_fonts_for_language(app):
    lang = app.font_lang_combo.get()
    font = app.font_script_combo.get()

    if not lang or lang == "Select Language":
        messagebox.showwarning("Select", "Choose a language from the dropdown.")
        return
    if not font or font == "Select Font":
        messagebox.showwarning("Select", "Choose a font/script from the dropdown.")
        return

    langdir = os.path.join(LANG_ROOT, lang)
    folder = os.path.join(langdir, FONTS_DIRNAME, font)
    mapping_file = os.path.join(folder, "mapping.csv")
    if not os.path.exists(mapping_file):
        messagebox.showerror("Missing", f"No mapping.csv in {font}")
        return

    mapping = load_csv(mapping_file, ["symbol","filename"])
    app.fonts_list.delete(*app.fonts_list.get_children())
    app.font_thumbnails = {}
    for row in mapping:
        sym = row.get("symbol","")
        fn = row.get("filename","")
        img_path = os.path.join(folder, fn)
        photo = None
        if os.path.exists(img_path):
            try:
                img = Image.open(img_path)
                img.thumbnail((32,32))
                photo = ImageTk.PhotoImage(img)
                app.font_thumbnails[sym] = photo
            except Exception as e:
                print("Thumbnail error:", e)
        app.fonts_list.insert("", "end", text=sym, values=(fn,), image=photo)

    app.current_font = (lang, font, folder)

def show_font_preview(app):
    sel = app.fonts_list.selection()
    if not sel or not getattr(app, "current_font", None):
        app.font_preview_label.config(image="", text="(no preview)")
        return
    item = sel[0]
    symbol = app.fonts_list.item(item, "text")
    filename = app.fonts_list.item(item, "values")[0]
    lang, fontname, folder = app.current_font
    img_path = os.path.join(folder, filename)
    if not os.path.exists(img_path):
        app.font_preview_label.config(image="", text="(missing image)")
        return
    try:
        img = Image.open(img_path)
        img.thumbnail((128,128))
        photo = ImageTk.PhotoImage(img)
        app.font_preview_label.config(image=photo, text="")
        app.font_preview_label.image = photo
    except Exception as e:
        app.font_preview_label.config(image="", text=f"(error: {e})")


def add_font_symbol(app):
    if not app.current_font:
        messagebox.showwarning("Load font", "Load a font mapping first.")
        return
    symbol = simpledialog.askstring("Symbol", "Symbol text (e.g. 'a' or 'mar'):")
    if not symbol:
        return
    imgp = filedialog.askopenfilename(filetypes=[("Images","*.png;*.svg;*.jpg;*.jpeg")])
    if not imgp:
        return
    lang, fontname, folder = app.current_font
    dest = os.path.join(folder, os.path.basename(imgp))
    shutil.copyfile(imgp, dest)
    mapping_file = os.path.join(folder, "mapping.csv")
    mapping = load_csv(mapping_file, ["symbol","filename"])
    mapping.append({"symbol": symbol, "filename": os.path.basename(imgp)})
    save_csv(mapping_file, ["symbol","filename"], mapping)
    load_fonts_for_language(app)



def replace_font_image(app):
    sel = app.fonts_list.selection()
    if not sel:
        messagebox.showwarning("Select", "Select a mapping row")
        return
    item = sel[0]
    symbol, filename = app.fonts_list.item(item, "values")
    new = filedialog.askopenfilename(filetypes=[("Images","*.png;*.svg;*.jpg;*.jpeg")])
    if not new:
        return
    lang, fontname, folder = app.current_font
    dest = os.path.join(folder, os.path.basename(new))
    shutil.copyfile(new, dest)
    mapping_file = os.path.join(folder, "mapping.csv")
    mapping = load_csv(mapping_file, ["symbol","filename"])
    for m in mapping:
        if m.get("symbol") == symbol and m.get("filename") == filename:
            m["filename"] = os.path.basename(new)
    save_csv(mapping_file, ["symbol","filename"], mapping)
    load_fonts_for_language(app)


def delete_font_symbol(app):
    sel = app.fonts_list.selection()
    if not sel:
        messagebox.showwarning("Select", "Select an entry")
        return
    item = sel[0]
    symbol, filename = app.fonts_list.item(item, "values")
    lang, fontname, folder = app.current_font
    if messagebox.askyesno("Delete", f"Delete mapping {symbol} -> {filename}?"):
        mapping_file = os.path.join(folder, "mapping.csv")
        mapping = load_csv(mapping_file, ["symbol","filename"])
        mapping = [m for m in mapping if not (m.get("symbol")==symbol and m.get("filename")==filename)]
        save_csv(mapping_file, ["symbol","filename"], mapping)
        try:
            os.remove(os.path.join(folder, filename))
        except Exception:
            pass
        load_fonts_for_language(app)


def save_current_font_mapping(app):
    if not app.current_font:
        messagebox.showwarning("No font", "Load font mapping first")
        return
    lang, fontname, folder = app.current_font
    rows = []
    for iid in app.fonts_list.get_children():
        sym, fn = app.fonts_list.item(iid, "values")
        rows.append({"symbol": sym, "filename": fn})
    save_csv(os.path.join(folder, "mapping.csv"), ["symbol","filename"], rows)
    messagebox.showinfo("Saved", "Font mapping saved")

def on_language_selected(event=None):
    lang = app.font_lang_combo.get()
    if not lang or lang == "Select Language":
        app.font_script_combo["values"] = []
        app.font_script_combo.set("Select Font")
        return
    langdir = os.path.join(LANG_ROOT, lang)
    fonts_dir = os.path.join(langdir, FONTS_DIRNAME)
    if not os.path.exists(fonts_dir):
        app.font_script_combo["values"] = []
        app.font_script_combo.set("Select Font")
        return
    fonts = [d for d in os.listdir(fonts_dir) if os.path.isdir(os.path.join(fonts_dir, d))]
    app.font_script_combo["values"] = fonts
    if fonts:
        app.font_script_combo.set(fonts[0])  # default to first

def populate_font_scripts(app):
    lang = app.font_lang_combo.get()
    if not lang or lang == "Select Language":
        app.font_script_combo["values"] = []
        app.font_script_combo.set("Select Font")
        return

    langdir = os.path.join(LANG_ROOT, lang)
    fonts_dir = os.path.join(langdir, FONTS_DIRNAME)
    if not os.path.exists(fonts_dir):
        app.font_script_combo["values"] = []
        app.font_script_combo.set("Select Font")
        return

    fonts = [d for d in os.listdir(fonts_dir) if os.path.isdir(os.path.join(fonts_dir, d))]
    app.font_script_combo["values"] = fonts
    if fonts:
        app.font_script_combo.set(fonts[0])  # default to first
    else:
        app.font_script_combo.set("Select Font")

