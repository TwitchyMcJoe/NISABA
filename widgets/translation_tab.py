import os, re
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

from constants import LANG_ROOT, GRAMMAR_TEXT, CONJ_FILE, CONJ_FIELDS, FONTS_DIRNAME, DICT_FILE, DICT_FIELDS
from utils.file_io import load_csv


def build_translation_tab(app):
    tab = ttk.Frame(app.notebook)
    app.notebook.add(tab, text="Translation")

    ttk.Label(tab, text="Translation Tool",
              font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=10, pady=(8, 4))

    # English → Conlang
    ttk.Label(tab, text="English → Conlang").pack(anchor="w", padx=8)
    app.trans_input = tk.Text(tab, height=4, wrap="word",
                              bg="#1b1b1b", fg="#eaeaea", insertbackground="white")
    app.trans_input.pack(fill="x", padx=8, pady=4)
    ttk.Button(tab, text="Translate to Conlang",
               command=lambda: translate_to_conlang(app)).pack(anchor="w", padx=8, pady=(0,6))

    # Conlang → English
    ttk.Label(tab, text="Conlang → English").pack(anchor="w", padx=8)
    app.trans_input_rev = tk.Text(tab, height=4, wrap="word",
                                  bg="#1b1b1b", fg="#eaeaea", insertbackground="white")
    app.trans_input_rev.pack(fill="x", padx=8, pady=4)
    ttk.Button(tab, text="Translate to English",
               command=lambda: translate_to_english(app)).pack(anchor="w", padx=8, pady=(0,6))

    # Result
    ttk.Label(tab, text="Result:").pack(anchor="w", padx=8)
    app.trans_output = tk.Text(tab, height=4, wrap="word",
                               bg="#1b1b1b", fg="#eaeaea", insertbackground="white")
    app.trans_output.pack(fill="x", padx=8, pady=4)

    # Pronunciation
    ttk.Label(tab, text="Pronunciation:").pack(anchor="w", padx=8)
    app.trans_pron = ttk.Label(tab, text="", background="#2b2b2b", foreground="lightblue")
    app.trans_pron.pack(anchor="w", padx=8, pady=(0,6))
    # Pronunciation playback
    play_frame = ttk.Frame(tab); play_frame.pack(anchor="w", padx=8, pady=(0,6))
    ttk.Button(play_frame, text="Play Pronunciation",
               command=lambda: play_pronunciation(app)).pack(side="left")

    # Glyph preview canvas
    ttk.Label(tab, text="Glyph Preview:").pack(anchor="w", padx=8)
    app.trans_canvas = tk.Canvas(tab, bg="white", height=200)
    app.trans_canvas.pack(fill="both", expand=True, padx=8, pady=8)
    app.trans_canvas.image_refs = []


# -------------------------
# Translation functions
# -------------------------

def translate_to_conlang(app):
    text = app.trans_input.get("1.0", tk.END).strip().lower()
    if not text: return
    if not app.dictionary:
        messagebox.showwarning("No dictionary", "Load a language first.")
        return

    words = text.split()
    out = []
    for w in words:
        entry = app.dictionary.get(w)
        if entry:
            con = entry.get("conlang","")
            pos = entry.get("pos","")
        else:
            con = f"[{w}]"
        out.append(con)

    result = " ".join(out)
    app.trans_output.delete("1.0", tk.END)
    app.trans_output.insert(tk.END, result)

    # Pronunciation (first word)
    first = words[0] if words else ""
    pron = ""
    if first and first in app.dictionary:
        pron = app.dictionary[first].get("pronunciation","")
    app.trans_pron.configure(text=pron or "—")

    # Render glyphs
    render_glyphs(app, result)


def translate_to_english(app):
    text = app.trans_input_rev.get("1.0", tk.END).strip().lower()
    if not text: return
    if not app.dictionary:
        messagebox.showwarning("No dictionary", "Load a language first.")
        return

    rev = {v.get("conlang","").lower(): k for k,v in app.dictionary.items()}
    words = text.split()
    out = []
    for w in words:
        eng = rev.get(w)
        out.append(eng if eng else f"[{w}]")

    result = " ".join(out)
    app.trans_output.delete("1.0", tk.END)
    app.trans_output.insert(tk.END, result)
    app.trans_pron.configure(text="—")

    render_glyphs(app, text)


# -------------------------
# Glyph rendering
# -------------------------

def render_glyphs(app, text):
    canvas = app.trans_canvas
    canvas.delete("all")
    canvas.image_refs = []

    if not app.current_language:
        return

    fontpath = os.path.join(LANG_ROOT, app.current_language, FONTS_DIRNAME)
    if not os.path.exists(fontpath):
        return
    fonts = [d for d in os.listdir(fontpath) if os.path.isdir(os.path.join(fontpath, d))]
    if not fonts:
        return
    mapping = load_csv(os.path.join(fontpath, fonts[0], "mapping.csv"), ["symbol","filename"])
    sym_map = {m["symbol"]: m["filename"] for m in mapping if m.get("symbol")}

    sorted_syms = sorted(sym_map.keys(), key=len, reverse=True)
    x, y, line_h = 10, 10, 60
    maxw = int(canvas.winfo_width() or 1000)
    i = 0
    L = len(text)
    while i < L:
        matched = False
        for sym in sorted_syms:
            if text[i:i+len(sym)] == sym:
                fn = sym_map[sym]
                path = os.path.join(fontpath, fonts[0], fn)
                if os.path.exists(path):
                    try:
                        im = Image.open(path)
                        desired_h = 50
                        w,h = im.size
                        scale = desired_h/h if h else 1.0
                        im2 = im.resize((int(w*scale), desired_h), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(im2)
                        canvas.create_image(x, y, anchor="nw", image=photo)
                        canvas.image_refs.append(photo)
                        x += im2.width + 4
                        line_h = max(line_h, im2.height + 5)
                    except Exception:
                        canvas.create_text(x, y, anchor="nw", text=sym, font=("Arial",18))
                        x += 12*len(sym)
                else:
                    canvas.create_text(x, y, anchor="nw", text=sym, font=("Arial",18))
                    x += 12*len(sym)
                i += len(sym); matched = True; break
        if not matched:
            ch = text[i]
            canvas.create_text(x, y, anchor="nw", text=ch, font=("Arial",18))
            x += 12; i += 1
        if x > maxw - 60:
            x = 10; y += line_h; line_h = 60

# -------------------------
# Pronunciation playback
# -------------------------

def play_pronunciation(app):
    ipa = app.trans_pron.cget("text").strip()
    if not ipa or ipa == "—":
        messagebox.showinfo("No pronunciation", "No pronunciation available to play.")
        return
    if not app.current_language:
        messagebox.showwarning("No language", "Load a language first.")
        return

    #ipa_folder = os.path.join(LANG_ROOT, app.current_language, "ipa_audio")
    from utils.file_io import get_ipa_audio_dir
    ipa_folder = get_ipa_audio_dir()


    if not os.path.exists(ipa_folder):
        messagebox.showinfo("No audio", f"No ipa_audio folder for {app.current_language}.")
        return

    played_any = False
    for ch in ipa:
        if ch in (" ", "/", "|"):
            continue
        found = False
        for ext in (".wav", ".mp3"):
            path = os.path.join(ipa_folder, f"{ch}{ext}")
            if os.path.exists(path):
                found = True; played_any = True
                try:
                    # Prefer pydub if available
                    try:
                        from pydub import AudioSegment
                        from pydub.playback import play as pydub_play
                        seg = AudioSegment.from_file(path)
                        pydub_play(seg)
                    except ImportError:
                        from playsound import playsound
                        playsound(path)
                except Exception as e:
                    print("Audio play error:", e)
                break
        if not found:
            print("No audio file for symbol:", ch)

    if not played_any:
        messagebox.showinfo("No audio", f"No audio files found for pronunciation: {ipa}")
