#!/usr/bin/env python3
"""Generate fio benchmark PPTX from Red Hat expressive template."""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import os

TEMPLATE = "./template.pptx"
OUTPUT = "./output/fio-benchmark-slides.pptx"
IMG_DIR = "./output"

# Colors
RH_RED = RGBColor(0xEE, 0x00, 0x00)
RH_DARK = RGBColor(0x15, 0x15, 0x15)
RH_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
RH_TEAL = RGBColor(0x14, 0x78, 0x78)
RH_BLUE = RGBColor(0x00, 0x66, 0xCC)
SAN_BLUE = RGBColor(0x00, 0x66, 0xCC)
NAS_RED = RGBColor(0xEE, 0x00, 0x00)
GRAY = RGBColor(0x6A, 0x6E, 0x73)
LIGHT_GRAY = RGBColor(0xD2, 0xD2, 0xD2)
GREEN = RGBColor(0x3E, 0x8D, 0x35)
DARK_TEAL = RGBColor(0x00, 0x4D, 0x4D)
BG_LIGHT = RGBColor(0xF5, 0xF5, 0xF5)

# Fonts
FONT_DISPLAY = "Red Hat Display"
FONT_DISPLAY_MED = "Red Hat Display Medium"
FONT_DISPLAY_SEMI = "Red Hat Display SemiBold"
FONT_TEXT = "Red Hat Text"
FONT_MONO = "Red Hat Mono"

# Slide dimensions (from template: 13.33" x 7.5")
SLIDE_W = Emu(12188950)
SLIDE_H = Emu(6858000)

# Layout indices (from template analysis)
LY_TITLE = 0          # TITLE_1: title + subtitle
LY_SECTION = 12       # CUSTOM_1_1_1_1_1: section divider with left accent
LY_CONTENT = 33       # title(0) + footer(1) + subtitle(2) + body(3) + header(4)
LY_TWO_COL = 36       # title(0) + footer(1) + header(2) + bodyL(3) + bodyR(4) + subtitle(5)
LY_BLANK = 26         # CUSTOM_...: blank/minimal
LY_CONTENT_NOCAP = 34 # title(0) + footer(1) + body(2) + header(3)


def delete_all_slides(prs):
    """Remove all existing slides from the presentation."""
    from lxml import etree
    prs_elem = prs.part._element
    ns = '{http://schemas.openxmlformats.org/presentationml/2006/main}'
    ns_r = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
    sldIdLst = prs_elem.find(f'{ns}sldIdLst')
    if sldIdLst is None:
        return
    for sldId in list(sldIdLst):
        rId = sldId.get(f'{ns_r}id')
        if rId:
            prs.part.drop_rel(rId)
        sldIdLst.remove(sldId)


def set_run(run, text, font_name=FONT_DISPLAY, size=Pt(18), color=RH_DARK, bold=False):
    run.text = text
    run.font.name = font_name
    run.font.size = size
    run.font.color.rgb = color
    run.font.bold = bold


def clear_and_set(placeholder, text, font_name=FONT_DISPLAY, size=Pt(18), color=RH_DARK,
                  bold=False, alignment=None):
    tf = placeholder.text_frame
    tf.clear()
    p = tf.paragraphs[0]
    if alignment:
        p.alignment = alignment
    run = p.add_run()
    set_run(run, text, font_name, size, color, bold)
    return tf


def add_bullet(tf, text, font_name=FONT_DISPLAY, size=Pt(16), color=RH_DARK, bold=False,
               level=0, space_before=Pt(6)):
    p = tf.add_paragraph()
    p.level = level
    p.space_before = space_before
    run = p.add_run()
    set_run(run, text, font_name, size, color, bold)
    return p


def add_mixed_bullet(tf, parts, level=0, space_before=Pt(6)):
    """Add a bullet with mixed formatting. parts = [(text, font, size, color, bold), ...]"""
    p = tf.add_paragraph()
    p.level = level
    p.space_before = space_before
    for text, font, size, color, bold in parts:
        run = p.add_run()
        set_run(run, text, font, size, color, bold)
    return p


def add_textbox(slide, left, top, width, height, text, font_name=FONT_DISPLAY,
                size=Pt(16), color=RH_DARK, bold=False, alignment=PP_ALIGN.LEFT,
                word_wrap=True):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = word_wrap
    p = tf.paragraphs[0]
    p.alignment = alignment
    run = p.add_run()
    set_run(run, text, font_name, size, color, bold)
    return txBox, tf


def add_table(slide, rows, cols, left, top, width, height):
    table_shape = slide.shapes.add_table(rows, cols, left, top, width, height)
    return table_shape.table


def style_table_cell(cell, text, font_name=FONT_DISPLAY, size=Pt(12), color=RH_DARK,
                     bold=False, alignment=PP_ALIGN.RIGHT, fill_color=None):
    cell.text = ""
    p = cell.text_frame.paragraphs[0]
    p.alignment = alignment
    run = p.add_run()
    set_run(run, text, font_name, size, color, bold)
    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
    if fill_color:
        cell.fill.solid()
        cell.fill.fore_color.rgb = fill_color


def style_header_cell(cell, text, font_name=FONT_DISPLAY_MED, size=Pt(11), color=RH_WHITE,
                      fill_color=RH_DARK, alignment=PP_ALIGN.CENTER):
    style_table_cell(cell, text, font_name, size, color, False, alignment, fill_color)
    cell.text_frame.paragraphs[0].runs[0].font.bold = True


def add_image_safe(slide, img_name, left, top, width=None, height=None):
    path = os.path.join(IMG_DIR, img_name)
    if os.path.exists(path):
        if width and height:
            slide.shapes.add_picture(path, left, top, width, height)
        elif width:
            slide.shapes.add_picture(path, left, top, width=width)
        elif height:
            slide.shapes.add_picture(path, left, top, height=height)
        else:
            slide.shapes.add_picture(path, left, top)
        return True
    return False


def add_rect(slide, left, top, width, height, fill_color, line_color=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if line_color:
        shape.line.color.rgb = line_color
        shape.line.width = Pt(1)
    else:
        shape.line.fill.background()
    return shape


# ============================================================
# Build presentation
# ============================================================
prs = Presentation(TEMPLATE)
delete_all_slides(prs)

# Margins / common positions
M_LEFT = Emu(885125)
M_TOP_TITLE = Emu(1100350)
M_TOP_SUB = Emu(1700000)
M_TOP_BODY = Emu(2200000)
BODY_W = Emu(10422000)
BODY_H = Emu(4000000)


# ============================================================
# Slide 1: Title
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[LY_TITLE])
# idx=0: Title
clear_and_set(slide.placeholders[0], "ontap-san vs ontap-nas\nfio Performance on OpenShift Virtualization",
              FONT_DISPLAY, Pt(36), RH_WHITE, bold=True)
# idx=1: Subtitle
clear_and_set(slide.placeholders[1], "iSCSI vs NFS with nconnect=8 — When does NAS beat SAN?",
              FONT_DISPLAY, Pt(20), RH_WHITE)
# idx=2, idx=3: bottom fields
clear_and_set(slide.placeholders[2], "OpenShift 4.22  |  NetApp AFF-C190  |  Trident CSI",
              FONT_DISPLAY, Pt(14), RH_WHITE)
clear_and_set(slide.placeholders[3], "RHEL 10 VM  |  fio benchmark",
              FONT_DISPLAY, Pt(14), RH_WHITE)


# ============================================================
# Slide 2: Methodology
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[LY_CONTENT])
clear_and_set(slide.placeholders[0], "Methodology — Ensuring a Fair Comparison",
              FONT_DISPLAY, Pt(28), RH_DARK, bold=True)
clear_and_set(slide.placeholders[2], "Why methodology matters for NFS vs iSCSI benchmarks",
              FONT_DISPLAY, Pt(14), RH_RED)

tf = slide.placeholders[3].text_frame
tf.clear()
tf.word_wrap = True

p = tf.paragraphs[0]
p.space_before = Pt(4)
run = p.add_run()
set_run(run, "NFS performance depends heavily on nconnect — default nconnect=1 severely under-utilizes NFS", FONT_DISPLAY, Pt(16), RH_DARK)

add_bullet(tf, "We enabled nconnect=8 via Trident nfsMountOptions to allow NFS full parallel throughput", FONT_DISPLAY, Pt(16), GREEN, bold=True)
add_bullet(tf, "fio's default random generator allows block re-reads → inflated results from ONTAP read cache", FONT_DISPLAY, Pt(16), RH_DARK)
add_bullet(tf, "We used random_generator=lfsr (each block accessed exactly once) to eliminate cache bias", FONT_DISPLAY, Pt(16), GREEN, bold=True)

# Key insight box
add_textbox(slide, M_LEFT, Emu(5000000), Emu(10422000), Emu(800000),
            "Key: nconnect=8 and LFSR are essential for a fair NFS benchmark — without them, NFS performance is dramatically underrepresented.",
            FONT_DISPLAY, Pt(15), RH_TEAL, bold=False)


# ============================================================
# Slide 3: Test Environment
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[LY_TWO_COL])
clear_and_set(slide.placeholders[0], "Infrastructure & Configuration",
              FONT_DISPLAY, Pt(28), RH_DARK, bold=True)
clear_and_set(slide.placeholders[5], "Test Environment",
              FONT_DISPLAY, Pt(14), RH_RED)

# Left column: Platform + Storage
tf_l = slide.placeholders[3].text_frame
tf_l.clear()
tf_l.word_wrap = True
p = tf_l.paragraphs[0]
run = p.add_run()
set_run(run, "Platform", FONT_DISPLAY_MED, Pt(18), RH_TEAL, bold=True)
add_bullet(tf_l, "OpenShift 4.22.0 + Virtualization 4.22.2", FONT_DISPLAY, Pt(14), RH_DARK)
add_bullet(tf_l, "3-node cluster, RHEL 10 VMs", FONT_DISPLAY, Pt(14), RH_DARK)
add_bullet(tf_l, "Data disk: 500Gi per VM", FONT_DISPLAY, Pt(14), RH_DARK)

add_bullet(tf_l, "", FONT_DISPLAY, Pt(8), RH_DARK)
p = tf_l.add_paragraph()
run = p.add_run()
set_run(run, "Storage", FONT_DISPLAY_MED, Pt(18), RH_TEAL, bold=True)
add_bullet(tf_l, "NetApp AFF-C190 (12× SSD, ADP, RAID-DP)", FONT_DISPLAY, Pt(14), RH_DARK)
add_bullet(tf_l, "10GbE connectivity", FONT_DISPLAY, Pt(14), RH_DARK)
add_bullet(tf_l, "Trident CSI driver", FONT_DISPLAY, Pt(14), RH_DARK)

# Right column: Benchmark + Protocols
tf_r = slide.placeholders[4].text_frame
tf_r.clear()
tf_r.word_wrap = True
p = tf_r.paragraphs[0]
run = p.add_run()
set_run(run, "Benchmark (fio)", FONT_DISPLAY_MED, Pt(18), RH_TEAL, bold=True)
add_bullet(tf_r, "direct=1, libaio, time_based", FONT_DISPLAY, Pt(14), RH_DARK)
add_bullet(tf_r, "runtime=120s, ramp_time=10s", FONT_DISPLAY, Pt(14), RH_DARK)
add_bullet(tf_r, "random_generator=lfsr", FONT_DISPLAY, Pt(14), RH_RED, bold=True)
add_bullet(tf_r, "3 iterations, average of iter 2-3", FONT_DISPLAY, Pt(14), RH_DARK)

add_bullet(tf_r, "", FONT_DISPLAY, Pt(8), RH_DARK)
p = tf_r.add_paragraph()
run = p.add_run()
set_run(run, "Three Protocols Compared", FONT_DISPLAY_MED, Pt(18), RH_TEAL, bold=True)
add_bullet(tf_r, "SAN — iSCSI (ontap-san)", FONT_DISPLAY, Pt(14), SAN_BLUE, bold=True)
add_bullet(tf_r, "NAS nc8 — NFS + nconnect=8 (ontap-nas)", FONT_DISPLAY, Pt(14), NAS_RED, bold=True)
add_bullet(tf_r, "NAS nc1 — NFS default (baseline)", FONT_DISPLAY, Pt(14), GRAY)


# ============================================================
# Slide 4: Test Matrix
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[LY_CONTENT])
clear_and_set(slide.placeholders[0], "Three Benchmarks, One Story",
              FONT_DISPLAY, Pt(28), RH_DARK, bold=True)
clear_and_set(slide.placeholders[2], "Test Matrix",
              FONT_DISPLAY, Pt(14), RH_RED)

tf = slide.placeholders[3].text_frame
tf.clear()
tf.word_wrap = True

# Test 1
p = tf.paragraphs[0]
run = p.add_run()
set_run(run, "Test 1 — Block Size Sweep  (Supplementary)", FONT_DISPLAY_MED, Pt(16), GRAY, bold=True)
add_bullet(tf, "4k–256k block sizes, iodepth=1 fixed. SAN wins uniformly — nconnect can't activate.", FONT_DISPLAY, Pt(14), GRAY, level=1)

add_bullet(tf, "", FONT_DISPLAY, Pt(6), RH_DARK)

# Test 2
p = tf.add_paragraph()
run = p.add_run()
set_run(run, "Test 2 — iodepth Sweep  ★ Core Finding", FONT_DISPLAY_MED, Pt(16), RH_RED, bold=True)
add_bullet(tf, "4k random, iodepth 1–128. SAN vs NAS nc8 vs NAS nc1.", FONT_DISPLAY, Pt(14), RH_DARK, level=1)
add_bullet(tf, "The heart of the story — read/write split with nconnect.", FONT_DISPLAY, Pt(14), RH_TEAL, level=1)

add_bullet(tf, "", FONT_DISPLAY, Pt(6), RH_DARK)

# Test 3
p = tf.add_paragraph()
run = p.add_run()
set_run(run, "Test 3 — Multi-VM Parallel  ★ Scalability", FONT_DISPLAY_MED, Pt(16), RH_RED, bold=True)
add_bullet(tf, "3VM and 6VM parallel, 4k random, iodepth 1–64.", FONT_DISPLAY, Pt(14), RH_DARK, level=1)
add_bullet(tf, "How each protocol scales when adding more VMs.", FONT_DISPLAY, Pt(14), RH_TEAL, level=1)


# ============================================================
# Slide 5: Section — Test 2
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[LY_SECTION])
clear_and_set(slide.placeholders[0], "Test 2\niodepth Sweep\nThe Read/Write Split",
              FONT_DISPLAY, Pt(36), RH_WHITE, bold=True)
clear_and_set(slide.placeholders[2], "4k random I/O, iodepth 1–128, single VM",
              FONT_DISPLAY, Pt(18), RH_WHITE)


# ============================================================
# Slide 6: Test 2 — Random Read (table + chart)
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[LY_CONTENT_NOCAP])
clear_and_set(slide.placeholders[0], "NAS nconnect=8 Dominates Read at Every Queue Depth",
              FONT_DISPLAY, Pt(24), RH_DARK, bold=True)

# Table
tbl = add_table(slide, 7, 4, Emu(500000), Emu(1850000), Emu(5400000), Emu(2800000))
headers = ["iodepth", "SAN (iSCSI)", "NAS nc8", "nc8 vs SAN"]
for i, h in enumerate(headers):
    style_header_cell(tbl.cell(0, i), h)

data = [
    ("1",   "4,394",   "9,502",   "NAS 2.2×"),
    ("4",   "21,302",  "41,657",  "NAS 2.0×"),
    ("16",  "65,668",  "160,243", "NAS 2.4×"),
    ("32",  "106,533", "196,958", "NAS 1.9×"),
    ("64",  "136,682", "203,091", "NAS 1.5×"),
    ("128", "135,911", "195,027", "NAS 1.4×"),
]
for r, row_data in enumerate(data):
    style_table_cell(tbl.cell(r+1, 0), row_data[0], size=Pt(12), alignment=PP_ALIGN.CENTER)
    style_table_cell(tbl.cell(r+1, 1), row_data[1], size=Pt(12), color=SAN_BLUE)
    style_table_cell(tbl.cell(r+1, 2), row_data[2], size=Pt(12), color=NAS_RED)
    style_table_cell(tbl.cell(r+1, 3), row_data[3], size=Pt(12), color=NAS_RED, bold=True, alignment=PP_ALIGN.CENTER)

# Key stats
add_textbox(slide, Emu(700000), Emu(4900000), Emu(2200000), Emu(600000),
            "Peak: NAS 2.4×", FONT_DISPLAY, Pt(28), NAS_RED, bold=True)
add_textbox(slide, Emu(3100000), Emu(4900000), Emu(2800000), Emu(600000),
            "NAS nc8 peak: 203K IOPS", FONT_DISPLAY, Pt(22), RH_TEAL, bold=True)

# Chart image
add_image_safe(slide, "fio-chart-iodepth-iops.png", Emu(6200000), Emu(1700000), width=Emu(5600000))


# ============================================================
# Slide 7: Test 2 — Random Write (table + chart)
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[LY_CONTENT_NOCAP])
clear_and_set(slide.placeholders[0], "SAN Wins Write at Every Queue Depth",
              FONT_DISPLAY, Pt(24), RH_DARK, bold=True)

tbl = add_table(slide, 7, 4, Emu(500000), Emu(1850000), Emu(5400000), Emu(2800000))
headers = ["iodepth", "SAN (iSCSI)", "NAS nc8", "Winner"]
for i, h in enumerate(headers):
    style_header_cell(tbl.cell(0, i), h)

data = [
    ("1",   "2,240",  "1,053",  "SAN 2.1×"),
    ("4",   "9,513",  "4,292",  "SAN 2.2×"),
    ("16",  "26,607", "23,327", "SAN 1.1×"),
    ("32",  "36,975", "30,837", "SAN 1.2×"),
    ("64",  "42,132", "32,869", "SAN 1.3×"),
    ("128", "42,771", "34,885", "SAN 1.2×"),
]
for r, row_data in enumerate(data):
    style_table_cell(tbl.cell(r+1, 0), row_data[0], size=Pt(12), alignment=PP_ALIGN.CENTER)
    style_table_cell(tbl.cell(r+1, 1), row_data[1], size=Pt(12), color=SAN_BLUE)
    style_table_cell(tbl.cell(r+1, 2), row_data[2], size=Pt(12), color=NAS_RED)
    style_table_cell(tbl.cell(r+1, 3), row_data[3], size=Pt(12), color=SAN_BLUE, bold=True, alignment=PP_ALIGN.CENTER)

add_textbox(slide, Emu(700000), Emu(4900000), Emu(2200000), Emu(600000),
            "Peak: SAN 2.2×", FONT_DISPLAY, Pt(28), SAN_BLUE, bold=True)
add_textbox(slide, Emu(3100000), Emu(4900000), Emu(2800000), Emu(600000),
            "SAN peak: 43K IOPS", FONT_DISPLAY, Pt(22), RH_TEAL, bold=True)

add_image_safe(slide, "fio-chart-hockey-stick.png", Emu(6200000), Emu(1700000), width=Emu(5600000))


# ============================================================
# Slide 8: nconnect Impact
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[LY_TWO_COL])
clear_and_set(slide.placeholders[0], "nconnect=8: Game-Changer for Read, Penalty for Write",
              FONT_DISPLAY, Pt(24), RH_DARK, bold=True)
clear_and_set(slide.placeholders[5], "nconnect Impact — nc8 vs nc1",
              FONT_DISPLAY, Pt(14), RH_RED)

# Left: Read advantage
tf_l = slide.placeholders[3].text_frame
tf_l.clear()
tf_l.word_wrap = True
p = tf_l.paragraphs[0]
run = p.add_run()
set_run(run, "Random Read", FONT_DISPLAY_MED, Pt(16), NAS_RED, bold=True)

add_bullet(tf_l, "", FONT_DISPLAY, Pt(4), RH_DARK)
p = tf_l.add_paragraph()
p.alignment = PP_ALIGN.CENTER
run = p.add_run()
set_run(run, "5.3×", FONT_DISPLAY, Pt(56), NAS_RED, bold=True)
p = tf_l.add_paragraph()
p.alignment = PP_ALIGN.CENTER
run = p.add_run()
set_run(run, "nc8 vs nc1 at iodepth=1", FONT_DISPLAY, Pt(14), GRAY)

add_bullet(tf_l, "", FONT_DISPLAY, Pt(8), RH_DARK)
add_bullet(tf_l, "Read scales with connection count", FONT_DISPLAY, Pt(14), RH_DARK)
add_bullet(tf_l, "Lock-free parallel access", FONT_DISPLAY, Pt(14), RH_DARK)
add_bullet(tf_l, "Up to 6.6× at iodepth=16", FONT_DISPLAY, Pt(14), RH_DARK)

# Right: Write penalty
tf_r = slide.placeholders[4].text_frame
tf_r.clear()
tf_r.word_wrap = True
p = tf_r.paragraphs[0]
run = p.add_run()
set_run(run, "Random Write", FONT_DISPLAY_MED, Pt(16), SAN_BLUE, bold=True)

add_bullet(tf_r, "", FONT_DISPLAY, Pt(4), RH_DARK)
p = tf_r.add_paragraph()
p.alignment = PP_ALIGN.CENTER
run = p.add_run()
set_run(run, "0.5×", FONT_DISPLAY, Pt(56), SAN_BLUE, bold=True)
p = tf_r.add_paragraph()
p.alignment = PP_ALIGN.CENTER
run = p.add_run()
set_run(run, "nc8 vs nc1 at iodepth=1", FONT_DISPLAY, Pt(14), GRAY)

add_bullet(tf_r, "", FONT_DISPLAY, Pt(8), RH_DARK)
add_bullet(tf_r, "Write gets slower with more connections", FONT_DISPLAY, Pt(14), RH_DARK)
add_bullet(tf_r, "ONTAP file-level lock contention", FONT_DISPLAY, Pt(14), RH_DARK)
add_bullet(tf_r, "nconnect=1 is faster for writes", FONT_DISPLAY, Pt(14), RH_DARK)

# Bottom insight
add_textbox(slide, M_LEFT, Emu(5700000), Emu(10422000), Emu(500000),
            "Why? Reads are lock-free — 8 connections scale in parallel. Writes on 8 connections create lock contention within ONTAP.",
            FONT_DISPLAY, Pt(14), RH_TEAL)


# ============================================================
# Slide 9: Section — Test 3
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[LY_SECTION])
clear_and_set(slide.placeholders[0], "Test 3\nMulti-VM Scalability\n3VM vs 6VM Parallel",
              FONT_DISPLAY, Pt(36), RH_WHITE, bold=True)
clear_and_set(slide.placeholders[2], "Does performance scale when you add more VMs?",
              FONT_DISPLAY, Pt(18), RH_WHITE)


# ============================================================
# Slide 10: 3VM Results
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[LY_CONTENT_NOCAP])
clear_and_set(slide.placeholders[0], "3VM: NAS Competes at Low Concurrency, Overtakes at High iodepth",
              FONT_DISPLAY, Pt(22), RH_DARK, bold=True)

tbl = add_table(slide, 9, 5, Emu(400000), Emu(1700000), Emu(6000000), Emu(3400000))
headers = ["Pattern", "iodepth", "SAN", "NAS nc8", "Winner"]
for i, h in enumerate(headers):
    style_header_cell(tbl.cell(0, i), h)

data = [
    ("randread",  "1",  "7,460",   "5,584",   "SAN 1.3×"),
    ("randread",  "4",  "30,888",  "23,079",  "SAN 1.3×"),
    ("randread",  "16", "83,059",  "71,570",  "SAN 1.2×"),
    ("randread",  "64", "102,983", "108,122", "NAS 1.05×"),
    ("randwrite", "1",  "6,649",   "5,395",   "SAN 1.2×"),
    ("randwrite", "4",  "24,010",  "20,065",  "SAN 1.2×"),
    ("randwrite", "16", "43,230",  "50,608",  "NAS 1.2×"),
    ("randwrite", "64", "50,355",  "70,838",  "NAS 1.4×"),
]
for r, row_data in enumerate(data):
    style_table_cell(tbl.cell(r+1, 0), row_data[0], size=Pt(11), alignment=PP_ALIGN.LEFT)
    style_table_cell(tbl.cell(r+1, 1), row_data[1], size=Pt(11), alignment=PP_ALIGN.CENTER)
    style_table_cell(tbl.cell(r+1, 2), row_data[2], size=Pt(11), color=SAN_BLUE)
    style_table_cell(tbl.cell(r+1, 3), row_data[3], size=Pt(11), color=NAS_RED)
    winner_color = NAS_RED if row_data[4].startswith("NAS") else SAN_BLUE
    style_table_cell(tbl.cell(r+1, 4), row_data[4], size=Pt(11), color=winner_color, bold=True, alignment=PP_ALIGN.CENTER)

add_image_safe(slide, "fio-chart-multivm.png", Emu(6600000), Emu(1700000), width=Emu(5200000))


# ============================================================
# Slide 11: 6VM Results
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[LY_CONTENT_NOCAP])
clear_and_set(slide.placeholders[0], "6VM: SAN Wins Every Pattern — NAS Hits the Ceiling",
              FONT_DISPLAY, Pt(24), RH_DARK, bold=True)

tbl = add_table(slide, 9, 5, Emu(400000), Emu(1700000), Emu(6000000), Emu(3400000))
headers = ["Pattern", "iodepth", "SAN", "NAS nc8", "Winner"]
for i, h in enumerate(headers):
    style_header_cell(tbl.cell(0, i), h)

data = [
    ("randread",  "1",  "14,869",  "10,707",  "SAN 1.4×"),
    ("randread",  "4",  "61,645",  "41,563",  "SAN 1.5×"),
    ("randread",  "16", "162,501", "92,993",  "SAN 1.7×"),
    ("randread",  "64", "207,877", "115,976", "SAN 1.8×"),
    ("randwrite", "1",  "13,986",  "10,238",  "SAN 1.4×"),
    ("randwrite", "4",  "46,829",  "33,754",  "SAN 1.4×"),
    ("randwrite", "16", "85,962",  "65,814",  "SAN 1.3×"),
    ("randwrite", "64", "99,924",  "73,809",  "SAN 1.4×"),
]
for r, row_data in enumerate(data):
    style_table_cell(tbl.cell(r+1, 0), row_data[0], size=Pt(11), alignment=PP_ALIGN.LEFT)
    style_table_cell(tbl.cell(r+1, 1), row_data[1], size=Pt(11), alignment=PP_ALIGN.CENTER)
    style_table_cell(tbl.cell(r+1, 2), row_data[2], size=Pt(11), color=SAN_BLUE)
    style_table_cell(tbl.cell(r+1, 3), row_data[3], size=Pt(11), color=NAS_RED)
    style_table_cell(tbl.cell(r+1, 4), row_data[4], size=Pt(11), color=SAN_BLUE, bold=True, alignment=PP_ALIGN.CENTER)

# Key insight on the right
add_textbox(slide, Emu(6800000), Emu(1900000), Emu(4800000), Emu(1200000),
            "NAS saturates at scale.\n6VM × iodepth 64:\nNAS latency 3,330 μs vs SAN 1,859 μs",
            FONT_DISPLAY, Pt(16), RH_TEAL, bold=False)

add_textbox(slide, Emu(6800000), Emu(3400000), Emu(4800000), Emu(800000),
            "Max SAN advantage: 1.8×\n(randread iodepth 64)",
            FONT_DISPLAY, Pt(24), SAN_BLUE, bold=True)

add_textbox(slide, Emu(6800000), Emu(4600000), Emu(4800000), Emu(700000),
            "The storage controller is the bottleneck — adding VMs can't push NAS further.",
            FONT_DISPLAY, Pt(14), GRAY)


# ============================================================
# Slide 12: Scale Factor
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[LY_CONTENT_NOCAP])
clear_and_set(slide.placeholders[0], "SAN Scales Linearly (2×); NAS Flatlines at High iodepth",
              FONT_DISPLAY, Pt(24), RH_DARK, bold=True)

tbl = add_table(slide, 9, 4, Emu(400000), Emu(1700000), Emu(5200000), Emu(3400000))
headers = ["Pattern", "iodepth", "SAN 3→6VM", "NAS 3→6VM"]
for i, h in enumerate(headers):
    style_header_cell(tbl.cell(0, i), h)

data = [
    ("randread",  "1",  "1.99×", "1.92×"),
    ("randread",  "4",  "2.00×", "1.80×"),
    ("randread",  "16", "1.96×", "1.30×"),
    ("randread",  "64", "2.02×", "1.07×"),
    ("randwrite", "1",  "2.10×", "1.90×"),
    ("randwrite", "4",  "1.95×", "1.68×"),
    ("randwrite", "16", "1.99×", "1.30×"),
    ("randwrite", "64", "1.98×", "1.04×"),
]
for r, row_data in enumerate(data):
    style_table_cell(tbl.cell(r+1, 0), row_data[0], size=Pt(12), alignment=PP_ALIGN.LEFT)
    style_table_cell(tbl.cell(r+1, 1), row_data[1], size=Pt(12), alignment=PP_ALIGN.CENTER)
    style_table_cell(tbl.cell(r+1, 2), row_data[2], size=Pt(12), color=SAN_BLUE, bold=True)
    # Highlight NAS values that show poor scaling
    nas_color = NAS_RED if row_data[3] in ("1.07×", "1.04×") else RH_DARK
    style_table_cell(tbl.cell(r+1, 3), row_data[3], size=Pt(12), color=nas_color, bold=(nas_color == NAS_RED))

add_image_safe(slide, "fio-chart-multivm-scale.png", Emu(5900000), Emu(1700000), width=Emu(5800000))

# Bottom insight
add_textbox(slide, Emu(400000), Emu(5300000), Emu(11000000), Emu(600000),
            "SAN: ~2.0× across the board — doubling VMs doubles throughput. NAS: 1.04–1.07× at high iodepth — adding VMs yields almost zero gain.",
            FONT_DISPLAY, Pt(15), RH_TEAL)


# ============================================================
# Slide 13: Test 1 Summary (supplementary)
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[LY_CONTENT_NOCAP])
clear_and_set(slide.placeholders[0], "Test 1 — Block Size Sweep (iodepth=1)  [Supplementary]",
              FONT_DISPLAY, Pt(24), RH_DARK, bold=True)

# Bullets on the left
_, tf = add_textbox(slide, Emu(400000), Emu(1700000), Emu(5800000), Emu(3000000),
                    "", FONT_DISPLAY, Pt(16), RH_DARK)
tf.word_wrap = True
p = tf.paragraphs[0]
run = p.add_run()
set_run(run, "At iodepth=1, nconnect=8 parallelism cannot activate — only one I/O in flight",
        FONT_DISPLAY, Pt(15), RH_DARK)
add_bullet(tf, "SAN wins every pattern by a consistent 1.1–1.8×", FONT_DISPLAY, Pt(15), RH_DARK)
add_bullet(tf, "Ratio stays flat regardless of block size — no crossover point", FONT_DISPLAY, Pt(15), RH_DARK)
add_bullet(tf, "LFSR is critical: without it, NAS seq read 256k reports 765 MiB/s — LFSR gives the true figure of 259 MiB/s (cache re-hits eliminated)",
           FONT_DISPLAY, Pt(15), RH_RED, bold=True)

add_textbox(slide, Emu(400000), Emu(5000000), Emu(5800000), Emu(600000),
            "Takeaway: At iodepth=1 SAN is consistently faster, but the story changes completely once concurrency increases.",
            FONT_DISPLAY, Pt(14), RH_TEAL)

add_image_safe(slide, "fio-chart-iops.png", Emu(6500000), Emu(1500000), width=Emu(5200000))


# ============================================================
# Slide 14: Conclusion — Workload Guidance
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[LY_TWO_COL])
clear_and_set(slide.placeholders[0], "Choosing the Right Protocol for Your Workload",
              FONT_DISPLAY, Pt(26), RH_DARK, bold=True)
clear_and_set(slide.placeholders[5], "Conclusion",
              FONT_DISPLAY, Pt(14), RH_RED)

# Left: Single VM
tf_l = slide.placeholders[3].text_frame
tf_l.clear()
tf_l.word_wrap = True
p = tf_l.paragraphs[0]
run = p.add_run()
set_run(run, "Single VM Guidance", FONT_DISPLAY_MED, Pt(18), RH_TEAL, bold=True)

add_bullet(tf_l, "", FONT_DISPLAY, Pt(4), RH_DARK)
p = tf_l.add_paragraph()
run = p.add_run()
set_run(run, "Read-Heavy Workloads:", FONT_DISPLAY_MED, Pt(16), NAS_RED, bold=True)
add_bullet(tf_l, "→ ontap-nas + nconnect=8", FONT_DISPLAY, Pt(15), NAS_RED, level=1)
add_bullet(tf_l, "1.4–2.4× faster than SAN", FONT_DISPLAY, Pt(14), RH_DARK, level=1)

add_bullet(tf_l, "", FONT_DISPLAY, Pt(4), RH_DARK)
p = tf_l.add_paragraph()
run = p.add_run()
set_run(run, "Write-Heavy Workloads:", FONT_DISPLAY_MED, Pt(16), SAN_BLUE, bold=True)
add_bullet(tf_l, "→ ontap-san (iSCSI)", FONT_DISPLAY, Pt(15), SAN_BLUE, level=1)
add_bullet(tf_l, "1.1–2.2× faster than NAS", FONT_DISPLAY, Pt(14), RH_DARK, level=1)

# Right: Multi-VM
tf_r = slide.placeholders[4].text_frame
tf_r.clear()
tf_r.word_wrap = True
p = tf_r.paragraphs[0]
run = p.add_run()
set_run(run, "Multi-VM Guidance", FONT_DISPLAY_MED, Pt(18), RH_TEAL, bold=True)

add_bullet(tf_r, "", FONT_DISPLAY, Pt(4), RH_DARK)
p = tf_r.add_paragraph()
run = p.add_run()
set_run(run, "Scaling VM Count:", FONT_DISPLAY_MED, Pt(16), SAN_BLUE, bold=True)
add_bullet(tf_r, "→ ontap-san", FONT_DISPLAY, Pt(15), SAN_BLUE, level=1)
add_bullet(tf_r, "Linear scaling (~2× per 2× VMs)", FONT_DISPLAY, Pt(14), RH_DARK, level=1)

add_bullet(tf_r, "", FONT_DISPLAY, Pt(4), RH_DARK)
p = tf_r.add_paragraph()
run = p.add_run()
set_run(run, "Few VMs + Deep Queue:", FONT_DISPLAY_MED, Pt(16), NAS_RED, bold=True)
add_bullet(tf_r, "→ ontap-nas competitive", FONT_DISPLAY, Pt(15), NAS_RED, level=1)
add_bullet(tf_r, "NAS overtakes at 3VM × iodepth 64", FONT_DISPLAY, Pt(14), RH_DARK, level=1)

# Bottom insight
add_textbox(slide, M_LEFT, Emu(5600000), Emu(10422000), Emu(600000),
            "The answer isn't \"SAN or NAS\" — it's \"what's your workload?\" Protocol choice should follow workload characteristics.",
            FONT_DISPLAY, Pt(16), RH_TEAL, bold=True)


# ============================================================
# Slide 15: nconnect Theme
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[LY_CONTENT])
clear_and_set(slide.placeholders[0], "The nconnect Story",
              FONT_DISPLAY, Pt(28), RH_DARK, bold=True)
clear_and_set(slide.placeholders[2], "Recurring Theme Throughout the Benchmarks",
              FONT_DISPLAY, Pt(14), RH_RED)

tf = slide.placeholders[3].text_frame
tf.clear()
tf.word_wrap = True

# The Setup
p = tf.paragraphs[0]
run = p.add_run()
set_run(run, "The Setup", FONT_DISPLAY_MED, Pt(18), RH_TEAL, bold=True)
add_bullet(tf, "NFS defaults to nconnect=1 — a single TCP connection that bottlenecks throughput", FONT_DISPLAY, Pt(15), RH_DARK)
add_bullet(tf, "One-line config change: nfsMountOptions in Trident backend → nconnect=8", FONT_DISPLAY, Pt(15), RH_DARK)

add_bullet(tf, "", FONT_DISPLAY, Pt(6), RH_DARK)

# Read win
p = tf.add_paragraph()
run = p.add_run()
set_run(run, "Read: Massive Win", FONT_DISPLAY_MED, Pt(18), NAS_RED, bold=True)
add_bullet(tf, "nc8 delivers 4–6.6× over nc1 for reads", FONT_DISPLAY, Pt(15), NAS_RED)
add_bullet(tf, "Outperforms even iSCSI at every queue depth", FONT_DISPLAY, Pt(15), RH_DARK)

add_bullet(tf, "", FONT_DISPLAY, Pt(6), RH_DARK)

# Write backfire
p = tf.add_paragraph()
run = p.add_run()
set_run(run, "Write: Backfire", FONT_DISPLAY_MED, Pt(18), SAN_BLUE, bold=True)
add_bullet(tf, "nc8 is slower than nc1 for writes — 8 connections contend on ONTAP write locks", FONT_DISPLAY, Pt(15), SAN_BLUE)
add_bullet(tf, "iSCSI has no equivalent multi-connection option (MC/S unimplemented in Linux/ONTAP)", FONT_DISPLAY, Pt(15), RH_DARK)

# Bottom
add_textbox(slide, M_LEFT, Emu(5400000), Emu(10422000), Emu(600000),
            "Practical advice: Always enable nconnect=8 for NFS — read gains far outweigh write penalty in most mixed workloads.",
            FONT_DISPLAY, Pt(15), RH_TEAL, bold=True)


# ============================================================
# Slide 16: Key Takeaways
# ============================================================
slide = prs.slides.add_slide(prs.slide_layouts[LY_CONTENT])
clear_and_set(slide.placeholders[0], "Key Takeaways",
              FONT_DISPLAY, Pt(32), RH_DARK, bold=True)
clear_and_set(slide.placeholders[2], "",
              FONT_DISPLAY, Pt(14), RH_RED)

tf = slide.placeholders[3].text_frame
tf.clear()
tf.word_wrap = True

p = tf.paragraphs[0]
p.space_before = Pt(8)
run = p.add_run()
set_run(run, "NAS + nconnect=8 is the best choice for read-heavy single-VM workloads (1.4–2.4× faster than SAN)",
        FONT_DISPLAY, Pt(17), RH_DARK)

add_bullet(tf, "SAN (iSCSI) is the best choice for write-heavy workloads and multi-VM scaling (linear 2× scaling)",
           FONT_DISPLAY, Pt(17), RH_DARK, space_before=Pt(16))

add_bullet(tf, "nconnect transforms NFS read performance (4–6.6× over default) but hurts write due to lock contention",
           FONT_DISPLAY, Pt(17), RH_DARK, space_before=Pt(16))

add_bullet(tf, "Use random_generator=lfsr in fio when benchmarking on ONTAP to prevent cache re-hits from inflating results",
           FONT_DISPLAY, Pt(17), RH_DARK, space_before=Pt(16))

add_bullet(tf, "NAS scalability has a ceiling — at 6VM × iodepth 64, throughput gains are only 1.04–1.07×",
           FONT_DISPLAY, Pt(17), RH_DARK, space_before=Pt(16))


# Save
prs.save(OUTPUT)
print(f"Saved to {OUTPUT}")
print(f"Total slides: {len(prs.slides)}")
