import os
import sys
import subprocess
from tkinter import filedialog, messagebox

def export_font_ttf(app):
    if not app.current_font:
        messagebox.showwarning("No font", "Load or create a font mapping first.")
        return

    lang, fontname, folder = app.current_font
    images_dir = folder

    out_path = filedialog.asksaveasfilename(
        defaultextension=".ttf",
        filetypes=[("TrueType Font", "*.ttf")],
        initialfile=f"{lang}_{fontname}.ttf"
    )
    if not out_path:
        return

    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "make_font_gpos.py"))

    cmd = [
        sys.executable, script_path,
        "--images", images_dir,
        "--out", out_path,
        "--family", f"{lang} {fontname}",
        "--style", "Regular",
        "--version", "1.000"
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        messagebox.showinfo("Exported", f"Font exported to {out_path}\n\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        msg = f"Font export failed:\n\nSTDOUT:\n{e.stdout}\n\nSTDERR:\n{e.stderr}"
        messagebox.showerror("Error", msg)
