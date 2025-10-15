import os
import tkinter as tk
from tkinter import Toplevel, Button, messagebox
from utils.audio_utils import play_audio_file
from utils.file_io import load_csv, ensure_language_dir   # <-- add ensure_language_dir here


def open_ipa_keyboard(app, target_entry, mode="full"):
    win = Toplevel(app)
    win.title("IPA Keyboard")

    if mode == "full":
        ipa_symbols = ["w","ʍ","x","y","ʏ","ʎ","z","ʐ","ʑ","ʒ","ʔ","ʕ","ʡ","ʢ","ʘ","β","θ","χ","ǃ","ǀ","ǁ","ǂ","a","ɐ","ɑ","ɒ","æ","b","ʙ","ɓ","c","ç","ɔ","ɕ","d","ɗ","ð","d͡z","d͡ʑ","d͡ʒ","ɖ","ɖ͡ʐ","e","ə","ɘ","ɛ","ɜ","ɞ","","g","ɢ","ɠ","ʛ","ɣ","ɤ","h","ʜ","ħ","ɦ","ɥ","ɧ","i","ɪ","ɨ","j","ɟ","ʄ","ʝ","k","kʼ","l","ʟ","ɭ","ɬ","ɮ","m","ɱ","ɯ","ɰ","n","ɴ","ɲ","ɳ","ŋ","o","ɵ","ø","ɶ","œ","p","pʼ","ɸ","q","r","ʀ","ɽ","ɹ","ɺ","ɻ","ɾ","ʁ","s","ʂ","sʼ","ʃ","t","tʼ","ʈ","t͡ɕ","t͡s","t͡ʃ","ʈ͡ʂ","u","ʉ","ʊ","v","ʋ","ʌ","ⱱ"]  # full set
    else:
        # restricted: load from phonology tables
        langdir = ensure_language_dir(app.current_language)
        rows = load_csv(os.path.join(langdir, "phonology.csv"), ["ipa","example","type","notes"])
        ipa_symbols = [r["ipa"] for r in rows if r.get("ipa")]

    from utils.file_io import get_ipa_audio_dir
    audio_dir = get_ipa_audio_dir()


    for idx, sym in enumerate(ipa_symbols):
        frame = tk.Frame(win)
        frame.grid(row=idx//6, column=(idx%6), padx=4, pady=4)

        btn = Button(frame, text=sym, width=4,
                     command=lambda s=sym: target_entry.insert(tk.END, s))
        btn.pack()

        play_btn = Button(frame, text="🔊", width=2,
                          command=lambda s=sym: play_symbol_audio(audio_dir, s))
        play_btn.pack()

def play_symbol_audio(audio_dir, symbol):
    filename = f"{symbol}.mp3"
    path = os.path.join(audio_dir, filename)
    if os.path.exists(path):
        play_audio_file(path)
    else:
        messagebox.showwarning("Missing", f"No audio file for IPA symbol '{symbol}'")
