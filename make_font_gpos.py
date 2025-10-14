#!/usr/bin/env python3
"""
SVG/PNG -> TTF font builder with:
- PNG tracing -> SVG (contour detection)
- Advance widths from bounding boxes
- GSUB ligature table for multi-character glyphs
- GPOS PairPos kerning (LookupType 2)
"""

import os, io, argparse
from typing import List, Tuple, Dict
from dataclasses import dataclass

from fontTools.ttLib import TTFont, newTable
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
from fontTools.ttLib.tables import otTables

from svgpathtools import svg2paths, Line, QuadraticBezier, CubicBezier
from PIL import Image
import numpy as np
from skimage import measure
from skimage.measure import approximate_polygon   # replacement

# ---------------- Defaults ----------------
DEFAULT_UPM = 1000
DEFAULT_ASCENT = 800
DEFAULT_DESCENT = -200
DEFAULT_ADVANCE = 600
ADVANCE_PADDING_RATIO = 0.1
MIN_ADVANCE = 200
PNG_THRESHOLD = 128
CONTOUR_TOLERANCE = 1.0
KERN_MARGIN = 30
DEFAULT_KERN_MIN = -200

ALIAS = {"comma": ",", "period": ".", "space": " ", "hyphen": "-", "dash": "-", "underscore": "_"}

# ---------------- Filename mapping ----------------
def filename_to_sequence(stem: str) -> List[str]:
    if stem in ALIAS:
        return [ALIAS[stem]]
    if "_" in stem:
        seq = []
        for p in stem.split("_"):
            if p in ALIAS: seq.append(ALIAS[p])
            elif len(p) == 1: seq.append(p)
            else: seq.extend(list(p))
        return seq
    return list(stem)

def sequence_to_glyphname(seq: List[str]) -> str:
    return "_".join("space" if ch == " " else ch for ch in seq)

# ---------------- PNG -> SVG tracing ----------------
def png_to_svg_pathlist(png_path: str) -> Tuple[List[str], Tuple[int,int]]:
    img = Image.open(png_path).convert("L")
    w,h = img.size
    arr = np.array(img)
    mask = (255 - arr) > PNG_THRESHOLD
    contours = measure.find_contours(mask.astype(float), level=0.5)
    paths = []
    for contour in contours:
        pts = [(float(c[1]), float(h - c[0])) for c in contour]
        if len(pts) < 3: continue
        pts_np = np.array(pts)
        try:
            pts_simpl = approximate_polygon(pts_np, tolerance=CONTOUR_TOLERANCE)
        except Exception:
            pts_simpl = pts_np
        pts_list = pts_simpl.tolist()
        if len(pts_list) < 3: continue
        if pts_list[0] != pts_list[-1]:
            pts_list.append(pts_list[0])
        d = [f"M {pts_list[0][0]} {pts_list[0][1]}"]
        for x,y in pts_list[1:]:
            d.append(f"L {x} {y}")
        d.append("Z")
        paths.append(" ".join(d))
    return paths, (w,h)

def svg_paths_to_svg_file(path_d_list: List[str], size: Tuple[int,int]) -> str:
    w,h = size
    sb = io.StringIO()
    sb.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">\n')
    for d in path_d_list:
        sb.write(f'  <path d="{d}" fill="black"/>\n')
    sb.write('</svg>\n')
    return sb.getvalue()

def ensure_svg_from_file(filepath: str) -> str:
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".svg": return filepath
    if ext == ".png":
        path_d_list, size = png_to_svg_pathlist(filepath)
        svg_text = svg_paths_to_svg_file(path_d_list, size)
        tmp_svg = filepath + ".trace.svg"
        with open(tmp_svg, "w", encoding="utf-8") as f:
            f.write(svg_text)
        return tmp_svg
    raise ValueError("Unsupported file type: " + ext)

# ---------------- Draw into TTGlyphPen ----------------
def draw_path_to_pen(paths, pen):
    for path in paths:
        started = False
        for seg in path:
            if not started:
                started = True
                pen.moveTo((seg.start.real, seg.start.imag))
            if isinstance(seg, Line):
                pen.lineTo((seg.end.real, seg.end.imag))
            elif isinstance(seg, QuadraticBezier):
                pen.qCurveTo((seg.control.real, seg.control.imag), (seg.end.real, seg.end.imag))
            elif isinstance(seg, CubicBezier):
                # fallback: ignore cubic for now
                pass
        if started:
            pen.closePath()

# ---------------- Metrics ----------------
@dataclass
class GlyphMetrics:
    name: str
    advance: int
    bbox: Tuple[int,int,int,int]

def compute_pair_gaps(glyphs: Dict[str, GlyphMetrics]) -> Dict[Tuple[str,str], int]:
    pairs = {}
    names = list(glyphs.keys())
    for L in names:
        for R in names:
            gL = glyphs[L]; gR = glyphs[R]
            xminL, yminL, xmaxL, ymaxL = gL.bbox
            xminR, yminR, xmaxR, ymaxR = gR.bbox
            gap = (gL.advance + xminR) - xmaxL
            if gap < KERN_MARGIN:
                kern = -(KERN_MARGIN - gap)
                kern = max(kern, DEFAULT_KERN_MIN)
                pairs[(L,R)] = int(kern)
    return pairs

# ---------------- Build GSUB ligature table ----------------
def build_gsub_ligature_table(font: TTFont, ligature_map: Dict[Tuple[str,...], str]):
    if not ligature_map:
        return

    gsub = newTable("GSUB")
    gsub.table = otTables.GSUB()

    # ScriptList
    scriptList = otTables.ScriptList()
    scriptRecord = otTables.ScriptRecord()
    scriptRecord.ScriptTag = "DFLT"
    script = otTables.Script()
    langSys = otTables.LangSys()
    langSys.LookupOrder = None
    langSys.ReqFeatureIndex = 0xFFFF
    langSys.FeatureIndex = [0]
    script.DefaultLangSys = langSys
    scriptRecord.Script = script
    scriptList.ScriptRecord = [scriptRecord]
    gsub.table.ScriptList = scriptList

    # FeatureList
    featureList = otTables.FeatureList()
    featureRecord = otTables.FeatureRecord()
    featureRecord.FeatureTag = "liga"
    feature = otTables.Feature()
    feature.FeatureParams = None
    feature.LookupListIndex = [0]
    featureRecord.Feature = feature
    featureList.FeatureRecord = [featureRecord]
    gsub.table.FeatureList = featureList

    # LookupList
    lookupList = otTables.LookupList()
    lookupList.Lookup = []

    lookup = otTables.Lookup()
    lookup.LookupType = 4  # ligature substitution
    lookup.LookupFlag = 0

    sub = otTables.LigatureSubst()
    sub.ligatures = {}
    for seq, ligname in ligature_map.items():
        first = seq[0]
        comps = list(seq[1:])
        ligrec = otTables.Ligature()
        ligrec.LigGlyph = ligname
        ligrec.Component = comps
        sub.ligatures.setdefault(first, []).append(ligrec)

    lookup.SubTable = [sub]
    lookupList.Lookup.append(lookup)
    gsub.table.LookupList = lookupList

    font["GSUB"] = gsub

# ---------------- Build GPOS PairPos ----------------
def build_gpos_pairpos(font: TTFont, kern_pairs: Dict[Tuple[str,str], int]):
    if not kern_pairs:
        return

    gpos = newTable("GPOS")
    gpos.table = otTables.GPOS()

    # ScriptList
    scriptList = otTables.ScriptList()
    scriptRecord = otTables.ScriptRecord()
    scriptRecord.ScriptTag = "DFLT"
    script = otTables.Script()
    langSys = otTables.LangSys()
    langSys.LookupOrder = None
    langSys.ReqFeatureIndex = 0xFFFF
    langSys.FeatureIndex = [0]
    script.DefaultLangSys = langSys
    scriptRecord.Script = script
    scriptList.ScriptRecord = [scriptRecord]
    gpos.table.ScriptList = scriptList

    # FeatureList
    featureList = otTables.FeatureList()
    featureRecord = otTables.FeatureRecord()
    featureRecord.FeatureTag = "kern"
    feature = otTables.Feature()
    feature.FeatureParams = None
    feature.LookupListIndex = [0]
    featureRecord.Feature = feature
    featureList.FeatureRecord = [featureRecord]
    gpos.table.FeatureList = featureList

    # LookupList
    lookupList = otTables.LookupList()
    lookupList.Lookup = []

    lookup = otTables.Lookup()
    lookup.LookupType = 2  # Pair Adjustment
    lookup.LookupFlag = 0

    # Organize pairs by first glyph
    pairs_by_first: Dict[str, List[Tuple[str,int]]] = {}
    for (L,R), val in kern_pairs.items():
        pairs_by_first.setdefault(L, []).append((R, val))

    # SubTable: PairPosFormat1
    sub = otTables.PairPos()
    sub.Format = 1
    sub.Coverage = None
    sub.PairSet = []
    sub.PairSetCount = 0

    # Coverage
    first_glyphs = sorted(pairs_by_first.keys())
    cov = otTables.Coverage()
    cov.format = 1
    cov.glyphs = first_glyphs
    sub.Coverage = cov

    # PairSets
    pairSets = []
    for first in first_glyphs:
        pairSet = otTables.PairSet()
        pairSet.PairValueRecord = []
        for (second, value) in pairs_by_first[first]:
            pvr = otTables.PairValueRecord()
            pvr.SecondGlyph = second
            valueRecord = otTables.ValueRecord()
            valueRecord.XAdvance = int(value)
            valueRecord.YAdvance = 0
            valueRecord.XPlacement = 0
            valueRecord.YPlacement = 0
            pvr.Value1 = None
            pvr.Value2 = valueRecord
            pairSet.PairValueRecord.append(pvr)
        pairSets.append(pairSet)

    sub.PairSet = pairSets
    sub.PairSetCount = len(pairSets)
    sub.ValueFormat1 = 0
    sub.ValueFormat2 = 0x0004  # XAdvance

    lookup.SubTable = [sub]
    lookupList.Lookup.append(lookup)
    gpos.table.LookupList = lookupList

    font["GPOS"] = gpos


# ---------------- Main font build ----------------
def build_font(images_dir: str, out_path: str, family: str, style: str, version: str,
               upm: int, ascent: int, descent: int, cubic_tolerance: float):

    font = TTFont()
    for tag in ["head","hhea","maxp","OS/2","hmtx","cmap","glyf","loca","name","post"]:
        font[tag] = newTable(tag)

    # Initialize dicts and .notdef glyph
    font["glyf"].glyphs = {}
    font["hmtx"].metrics = {}
    notdef_pen = TTGlyphPen(None)
    box_size = DEFAULT_ADVANCE
    notdef_pen.moveTo((0, 0))
    notdef_pen.lineTo((box_size, 0))
    notdef_pen.lineTo((box_size, box_size))
    notdef_pen.lineTo((0, box_size))
    notdef_pen.closePath()
    notdef_glyph = notdef_pen.glyph()
    font["glyf"].glyphs[".notdef"] = notdef_glyph
    font["hmtx"].metrics[".notdef"] = (DEFAULT_ADVANCE, 0)

    # Fully initialize head table
    import time
    head = font["head"]
    head.tableVersion = 1.0
    head.fontRevision = 1.0
    head.checkSumAdjustment = 0
    head.magicNumber = 0x5F0F3CF5
    head.flags = 3
    head.unitsPerEm = upm
    head.created = head.modified = int(time.time())
    head.macStyle = 0
    head.lowestRecPPEM = 8
    head.indexToLocFormat = 0
    head.glyphDataFormat = 0

    # Fully initialize hhea (fixes fontDirectionHint error)
    hhea = font["hhea"]
    hhea.ascent = ascent
    hhea.descent = descent
    hhea.lineGap = 0
    hhea.advanceWidthMax = DEFAULT_ADVANCE
    hhea.minLeftSideBearing = 0
    hhea.minRightSideBearing = 0
    hhea.xMaxExtent = DEFAULT_ADVANCE
    hhea.caretSlopeRise = 1
    hhea.caretSlopeRun = 0
    hhea.caretOffset = 0
    hhea.reserved0 = hhea.reserved1 = hhea.reserved2 = hhea.reserved3 = 0
    hhea.metricDataFormat = 0
    hhea.fontDirectionHint = 2  # required

    # OS/2 basic metrics
    os2 = font["OS/2"]
    os2.usWinAscent = ascent
    os2.usWinDescent = abs(descent)
    os2.sTypoAscender = ascent
    os2.sTypoDescender = descent
    os2.sTypoLineGap = 0
    os2.fsSelection = 0

    # Name table
    name_table = font["name"]; name_table.names = []
    if not hasattr(name_table, "format"):
        name_table.format = 0
    def add_name(nameID, string): name_table.setName(string, nameID, 3, 1, 0x409)
    add_name(1, family); add_name(2, style); add_name(3, f"{family}-{style}")
    add_name(4, f"{family} {style}"); add_name(5, version)
    add_name(6, f"{family.replace(' ','')}-{style}")

    # Collect glyphs
    glyph_order = [".notdef"]

    cmap_table = font["cmap"]; cmap_table.tableVersion = 0; cmap_table.tables = []
    cmap = CmapSubtable.newSubtable(4)
    cmap.platformID = 3; cmap.platEncID = 1; cmap.language = 0; cmap.cmap = {}
    cmap_table.tables.append(cmap)

    glyph_metrics: Dict[str,GlyphMetrics] = {}
    ligature_map: Dict[Tuple[str,...], str] = {}

    for filename in sorted(os.listdir(images_dir)):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in (".svg",".png"): continue
        print(f"Processing {filename}...")
        try:
            stem = os.path.splitext(filename)[0]
            seq_chars = filename_to_sequence(stem)
            glyph_name = sequence_to_glyphname(seq_chars)
            src_path = os.path.join(images_dir, filename)
            svg_path = ensure_svg_from_file(src_path)
            paths, _ = svg2paths(svg_path)
            pen = TTGlyphPen(None)
            draw_path_to_pen(paths, pen)
            glyph = pen.glyph()
            try:
                xmin,ymin,xmax,ymax = glyph.boundingBox()
            except Exception:
                xmin=ymin=0; xmax=ymax=DEFAULT_ADVANCE
            width = max(xmax-xmin, MIN_ADVANCE)
            advance = max(int(width*(1+ADVANCE_PADDING_RATIO)), MIN_ADVANCE)

            font["glyf"].glyphs[glyph_name] = glyph
            font["hmtx"].metrics[glyph_name] = (advance,0)
            glyph_order.append(glyph_name)

            if len(seq_chars)==1 and ord(seq_chars[0])<0x110000:
                cmap.cmap[ord(seq_chars[0])] = glyph_name
            if len(seq_chars)>1:
                seq_gnames = tuple(sequence_to_glyphname([ch]) for ch in seq_chars)
                ligature_map[seq_gnames] = glyph_name

            glyph_metrics[glyph_name] = GlyphMetrics(
                glyph_name, advance, (int(xmin),int(ymin),int(xmax),int(ymax))
            )
            print(f"[OK] Finished {filename} -> {glyph_name}")

        except Exception as e:
            print(f"[WARN] Skipping {filename}: {e}")
            continue

    # Finalize glyph order once, unique, with .notdef first
    unique_order = []
    seen = set()
    for g in glyph_order:
        if g not in seen:
            unique_order.append(g)
            seen.add(g)
    font.setGlyphOrder(unique_order)

    # Required table field finalizations
    maxp = font["maxp"]
    maxp.tableVersion = 0x00010000
    maxp.numGlyphs = len(font.getGlyphOrder())
    maxp.maxPoints = 0
    maxp.maxContours = 0
    maxp.maxCompositePoints = 0
    maxp.maxCompositeContours = 0
    maxp.maxZones = 2
    maxp.maxTwilightPoints = 0
    maxp.maxStorage = 0
    maxp.maxFunctionDefs = 0
    maxp.maxInstructionDefs = 0
    maxp.maxStackElements = 0
    maxp.maxSizeOfInstructions = 0
    maxp.maxComponentElements = 0
    maxp.maxComponentDepth = 0

    hhea.numberOfHMetrics = len(font["hmtx"].metrics)

    post = font["post"]
    post.formatType = 3.0
    post.italicAngle = 0
    post.underlinePosition = -75
    post.underlineThickness = 50
    post.isFixedPitch = 0
    post.minMemType42 = 0
    post.maxMemType42 = 0
    post.minMemType1 = 0
    post.maxMemType1 = 0

    if ligature_map:
        build_gsub_ligature_table(font, ligature_map)

    kern_pairs = compute_pair_gaps(glyph_metrics)
    if kern_pairs:
        build_gpos_pairpos(font, kern_pairs)

    # Sanity: remove any stray GlyphOrder table
    if "GlyphOrder" in font:
        print("[WARN] Removing unexpected table GlyphOrder")
        del font["GlyphOrder"]

    font.save(out_path)
    print(f"[DONE] Saved {out_path}. Glyphs: {len(font.getGlyphOrder())-1}, ligatures: {len(ligature_map)}, kern pairs: {len(kern_pairs)}")

# ---------------- CLI ----------------
def parse_args():
    p = argparse.ArgumentParser(description="Build TTF with GPOS kerning from SVG/PNG glyphs")
    p.add_argument("--images", "-i", required=True, help="Directory with SVG/PNG glyph files")
    p.add_argument("--out", "-o", default="CustomFont.ttf", help="Output TTF path")
    p.add_argument("--family", default="Custom Font")
    p.add_argument("--style", default="Regular")
    p.add_argument("--version", default="1.000")
    p.add_argument("--upm", type=int, default=DEFAULT_UPM)
    p.add_argument("--ascent", type=int, default=DEFAULT_ASCENT)
    p.add_argument("--descent", type=int, default=DEFAULT_DESCENT)
    p.add_argument("--tol", type=float, default=0.75)
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    build_font(args.images, args.out, args.family, args.style, args.version,
               args.upm, args.ascent, args.descent, args.tol)
