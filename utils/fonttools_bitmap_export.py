# utils/fonttools_bitmap_export.py
import os
from PIL import Image
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
from tkinter import filedialog, messagebox

DEFAULT_UPM = 1000
DEFAULT_ASCENT = 800
DEFAULT_DESCENT = -200
DEFAULT_ADVANCE = 600
PUA_START = 0xE000  # Private Use Area start
STRIKE_PPEM = 64    # bitmap strike size in pixels (height)

def _assign_codepoint(symbol, used, pua_next):
    # Single real Unicode character -> use its codepoint
    if len(symbol) == 1 and ord(symbol) < 0x110000:
        cp = ord(symbol)
        # Ensure unique assignment
        while cp in used:
            cp = pua_next
            pua_next += 1
    else:
        cp = pua_next
        pua_next += 1
    used.add(cp)
    return cp, pua_next

def export_font_ttf_bitmap(app):
    if not app.current_font:
        messagebox.showwarning("No font", "Load or create a font mapping first.")
        return

    lang, fontname, folder = app.current_font
    mapping_file = os.path.join(folder, "mapping.csv")
    if not os.path.exists(mapping_file):
        messagebox.showerror("Missing", f"No mapping.csv in {folder}")
        return

    # Load mapping rows (symbol, filename)
    try:
        from utils.file_io import load_csv
        rows = load_csv(mapping_file, ["symbol", "filename"])
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load mapping.csv: {e}")
        return

    if not rows:
        messagebox.showwarning("Empty", "No symbols in mapping.csv")
        return

    out_path = filedialog.asksaveasfilename(
        defaultextension=".ttf",
        filetypes=[("TrueType/OpenType Font", "*.ttf")],
        initialfile=f"{lang}_{fontname}_bitmap.ttf",
        title="Export Font (Bitmap TTF)"
    )
    if not out_path:
        return

    # Build base font
    font = TTFont()
    for tag in ["head","hhea","maxp","OS/2","hmtx","cmap","name","post"]:
        font[tag] = newTable(tag)

    # name table metadata
    name_table = font["name"]
    name_table.names = []
    if not hasattr(name_table, "format"):
        name_table.format = 0
    def add_name(nameID, string): name_table.setName(string, nameID, 3, 1, 0x409)
    family = f"{lang} {fontname}"
    style = "Regular"
    version = "1.000"
    add_name(1, family); add_name(2, style); add_name(3, f"{family}-{style}")
    add_name(4, f"{family} {style}"); add_name(5, version)
    add_name(6, f"{family.replace(' ','')}-{style}")

    # head
    import time
    head = font["head"]
    head.tableVersion = 1.0
    head.fontRevision = 1.0
    head.checkSumAdjustment = 0
    head.magicNumber = 0x5F0F3CF5
    head.flags = 3
    head.unitsPerEm = DEFAULT_UPM
    head.created = head.modified = int(time.time())
    head.macStyle = 0
    head.lowestRecPPEM = 8
    head.indexToLocFormat = 0
    head.glyphDataFormat = 0

    # hhea
    hhea = font["hhea"]
    hhea.ascent = DEFAULT_ASCENT
    hhea.descent = DEFAULT_DESCENT
    hhea.lineGap = 0
    hhea.advanceWidthMax = DEFAULT_ADVANCE
    hhea.minLeftSideBearing = 0
    hhea.minRightSideBearing = 0
    hhea.xMaxExtent = DEFAULT_ADVANCE
    hhea.caretSlopeRise = 1
    hhea.caretSlopeRun = 0
    hhea.caretOffset = 0
    hhea.metricDataFormat = 0
    hhea.numberOfHMetrics = 0  # set later

    # OS/2
    os2 = font["OS/2"]
    os2.usWinAscent = DEFAULT_ASCENT
    os2.usWinDescent = abs(DEFAULT_DESCENT)
    os2.sTypoAscender = DEFAULT_ASCENT
    os2.sTypoDescender = DEFAULT_DESCENT
    os2.sTypoLineGap = 0
    os2.fsSelection = 0x040  # Regular

    # post
    post = font["post"]
    post.formatType = 3.0
    post.italicAngle = 0
    post.underlinePosition = -75
    post.underlineThickness = 50
    post.isFixedPitch = 0

    # cmap (platform 3, encoding 1: Windows Unicode BMP)
    cmap_table = font["cmap"]
    cmap_table.tableVersion = 0
    cmap_table.tables = []
    cmap = CmapSubtable.newSubtable(4)
    cmap.platformID = 3
    cmap.platEncID = 1
    cmap.language = 0
    cmap.cmap = {}
    cmap_table.tables.append(cmap)

    # hmtx
    hmtx = font["hmtx"]
    hmtx.metrics = {}

    # Glyph order: we still need glyph names; bitmap glyphs use .notdef + named glyphs
    glyph_order = [".notdef"]
    hmtx.metrics[".notdef"] = (DEFAULT_ADVANCE, 0)

    # Build CBLC/CBDT for bitmap strikes
    cblc = newTable("CBLC")
    cbdt = newTable("CBDT")
    font["CBLC"] = cblc
    font["CBDT"] = cbdt

    # Initialize CBLC structures
    from fontTools.ttLib.tables.C_B_D_T_ import Strike as CBDTStrike
    from fontTools.ttLib.tables.C_B_L_C_ import Strike as CBLStrike
    cblc.strikes = []
    cbdt.strikes = []

    # One strike at STRIKE_PPEM
    cbl_strike = CBLStrike(STRIKE_PPEM, STRIKE_PPEM)
    cblc.strikes.append(cbl_strike)
    cbdt_strike = CBDTStrike(STRIKE_PPEM, STRIKE_PPEM)
    cbdt.strikes.append(cbdt_strike)

    used_codepoints = set()
    pua_next = PUA_START

    # Load and assign each mapping row
    for row in rows:
        symbol = (row.get("symbol") or "").strip()
        filename = (row.get("filename") or "").strip()
        if not symbol or not filename:
            continue
        img_path = os.path.join(folder, filename)
        if not os.path.exists(img_path):
            continue

        # Assign codepoint
        codepoint, pua_next = _assign_codepoint(symbol, used_codepoints, pua_next)

        # Glyph name (based on symbol if 1-char, else "gXXXX")
        glyph_name = symbol if len(symbol) == 1 else f"g{codepoint:X}"
        glyph_order.append(glyph_name)
        cmap.cmap[codepoint] = glyph_name

        # Advance width heuristic from image width
        try:
            im = Image.open(img_path).convert("RGBA")
        except Exception:
            # Skip unreadable images
            continue

        # Scale image to strike height, keep aspect
        w, h = im.size
        if h <= 0 or w <= 0:
            continue
        scale = STRIKE_PPEM / float(h)
        new_w = max(1, int(round(w * scale)))
        im_resized = im.resize((new_w, STRIKE_PPEM), Image.Resampling.LANCZOS)

        # Save glyph bitmap into CBDT strike
        # CBDT expects PNG bytes
        import io
        buf = io.BytesIO()
        im_resized.save(buf, format="PNG")
        png_bytes = buf.getvalue()
        buf.close()

        cbdt_strike.bitmaps[glyph_name] = png_bytes

        # CBLC index entry
        # Minimal index using default metrics; top/left bearings 0
        cbl_strike.setGlyphMetrics(glyph_name, (0, 0, new_w, STRIKE_PPEM))

        # Set advance width (monospace-ish or image width + padding)
        advance = max(DEFAULT_ADVANCE, int(new_w * (DEFAULT_UPM / STRIKE_PPEM)))
        hmtx.metrics[glyph_name] = (advance, 0)

    # Finalize metrics count
    hhea.numberOfHMetrics = len(hmtx.metrics)

    # Set glyph order and maxp
    font.setGlyphOrder(glyph_order)
    maxp = newTable("maxp")
    maxp.tableVersion = 0x00010000
    maxp.numGlyphs = len(glyph_order)
    font["maxp"] = maxp

    # Save
    try:
        font.save(out_path)
        messagebox.showinfo("Exported", f"Bitmap font exported to:\n{out_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save font: {e}")
