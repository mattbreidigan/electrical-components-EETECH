"""
Recreated label / chip-mark artwork for the storage-media modeling study.

All artwork is drawn from scratch with Pillow (no manufacturer photos, no brand
font files). Typography uses stock system fonts as stand-ins. Output -> refs/textures/.

Run:  python build/make_labels.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(__file__), "..", "refs", "textures")
os.makedirs(OUT, exist_ok=True)

FONTS = r"C:\Windows\Fonts"
def F(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)

ARI      = "arial.ttf"
ARI_B    = "arialbd.ttf"
ARI_I    = "ariali.ttf"
MONO     = "consola.ttf"
MONO_B   = "consolab.ttf"
THIN     = "segoeuil.ttf"
SEMI     = "segoeuisl.ttf"

ORANGE = (238, 123, 32)
WHITE  = (242, 242, 242)
GREY   = (140, 140, 142)
DGREY  = (95, 95, 98)


# ----------------------------------------------------------------------------- helpers
def text_tracked(draw, xy, s, font, fill, tracking=0, anchor_l=True):
    """Draw string with extra per-glyph tracking (px). Returns total width."""
    x, y = xy
    if not anchor_l:
        w = sum(draw.textlength(c, font=font) + tracking for c in s) - tracking
        x -= w
    for c in s:
        draw.text((x, y), c, font=font, fill=fill)
        x += draw.textlength(c, font=font) + tracking
    return x - xy[0]


def tracked_width(draw, s, font, tracking=0):
    return sum(draw.textlength(c, font=font) + tracking for c in s) - (tracking if s else 0)


def center_tracked(draw, cx, y, s, font, fill, tracking=0):
    w = tracked_width(draw, s, font, tracking)
    text_tracked(draw, (cx - w / 2, y), s, font, fill, tracking)


def barcode(draw, x, y, w, h, seed=12345):
    """Deterministic pseudo Code-128 look."""
    rnd = seed
    cx = x
    while cx < x + w:
        rnd = (1103515245 * rnd + 12345) & 0x7FFFFFFF
        bw = 2 + (rnd >> 8) % 5
        if (rnd >> 4) & 1:
            draw.rectangle([cx, y, cx + bw, y + h], fill=(20, 20, 20))
        cx += bw
    # quiet zone + text handled by caller


def rrect(draw, box, r, fill=None, outline=None, width=1):
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


# ----------------------------------------------------------------------------- 970 EVO top label
def m2_label():
    # label decal only; real label ~ 73 x 20 mm  -> 3.65:1
    W, H = 4096, 1122
    im = Image.new("RGB", (W, H), (24, 24, 27))
    d = ImageDraw.Draw(im)

    # very subtle top sheen band
    for i in range(H // 3):
        a = int(8 * (1 - i / (H / 3)))
        d.line([(0, i), (W, i)], fill=(24 + a, 24 + a, 27 + a))

    m = 150  # left margin
    # V-NAND SSD  (small caps, tracked)
    d.text((m, 120), "V-NAND SSD", font=F(SEMI, 92), fill=WHITE)

    # 970 EVO  headline
    big = F(ARI_B, 388)
    y0 = 232
    x = m - 10
    d.text((x, y0), "970", font=big, fill=WHITE)
    x += d.textlength("970", font=big) + 56
    d.text((x, y0), "EVO", font=big, fill=ORANGE)
    x += d.textlength("EVO", font=big)

    # orange rule
    d.rectangle([m, y0 + 424, x, y0 + 440], fill=ORANGE)

    # NVMe M.2
    d.text((m, y0 + 476), "NVMe M.2", font=F(ARI, 138), fill=WHITE)
    # maker line
    d.text((m, y0 + 672), "SAMSUNG ELECTRONICS CO., LTD.", font=F(ARI, 58), fill=GREY)

    # capacity block (right-centre)
    cap = "500GB"
    capf = F(ARI, 196)
    cw = d.textlength(cap, font=capf)
    d.text((W - 1180 - cw / 2, H / 2 - 130), cap, font=capf, fill=WHITE)

    # SAMSUNG wordmark near connector end (far right), tracked
    text_tracked(d, (W - 250, 150), "SAMSUNG", F(ARI_B, 96), WHITE, tracking=14, anchor_l=False)

    # faint spec line lower right
    d.text((W - 250 - tracked_width(d, "PCIe Gen 3.0 x4  NVMe 1.3", F(MONO, 50), 2),
            H - 180), "PCIe Gen 3.0 x4  NVMe 1.3", font=F(MONO, 50), fill=DGREY)

    im.save(os.path.join(OUT, "tex_m2_label.png"))
    print("wrote tex_m2_label.png", im.size)


def m2_label_back():
    """Copper heat-spreader film underside with faint reversed etch."""
    W, H = 2048, 561
    im = Image.new("RGB", (W, H), (150, 92, 58))
    d = ImageDraw.Draw(im)
    for i in range(H):
        a = int(18 * (i / H) - 9)
        d.line([(0, i), (W, i)], fill=(150 + a, 92 + a // 2, 58 + a // 3))
    d.text((90, 150), "SAMSUNG  V-NAND  HEAT SPREADER", font=F(MONO, 40), fill=(120, 74, 46))
    d.text((90, 230), "THIN COPPER FILM", font=F(MONO, 40), fill=(120, 74, 46))
    im = im.transpose(Image.FLIP_LEFT_RIGHT)
    im.save(os.path.join(OUT, "tex_m2_label_back.png"))
    print("wrote tex_m2_label_back.png", im.size)


# ----------------------------------------------------------------------------- chip top marks
def chip_mark(fname, lines, bg=(16, 16, 18), fg=(120, 120, 124), size=(1024, 1024), rot=0):
    im = Image.new("RGB", size, bg)
    d = ImageDraw.Draw(im)
    # pin-1 dot (corner)
    d.ellipse([70, size[1]-150, 150, size[1]-70], fill=(fg[0]-45, fg[1]-45, fg[2]-45))
    fs0, fs1 = 84, 62
    total = fs0 + 22 + (len(lines) - 1) * (fs1 + 14)
    y = (size[1] - total) / 2
    for i, ln in enumerate(lines):
        f = F(MONO_B if i == 0 else MONO, fs0 if i == 0 else fs1)
        w = d.textlength(ln, font=f)
        d.text(((size[0] - w) / 2, y), ln, font=f, fill=fg)
        y += (fs0 + 22) if i == 0 else (fs1 + 14)
    if rot:
        im = im.rotate(rot, expand=True)
    im.save(os.path.join(OUT, fname))
    print("wrote", fname, im.size)


def _hatch(d, box, step, fill, w=1):
    x0, y0, x1, y1 = box
    x = x0 - (y1 - y0)
    while x < x1:
        d.line([(x, y0), (x + (y1 - y0), y1)], fill=fill, width=w)
        x += step


def _bga(d, cx, cy, nx, ny, pitch, r, fill):
    for i in range(nx):
        for j in range(ny):
            x = cx + (i - (nx - 1) / 2) * pitch
            y = cy + (j - (ny - 1) / 2) * pitch
            d.ellipse([x - r, y - r, x + r, y + r], fill=fill)


def pcb_m2():
    """970 EVO PCB top artwork: black mask, gold pads, white silk. 80.15 x 22.15."""
    W, H = 4096, 1132
    mmx = W / 80.15
    im = Image.new("RGB", (W, H), (10, 11, 12))
    d = ImageDraw.Draw(im)
    GOLD = (196, 150, 74)
    SILK = (205, 206, 208)
    COPP = (24, 24, 22)

    # ground pour hatch over most of board
    _hatch(d, (int(6 * mmx), 40, int(78 * mmx), H - 40), 26, COPP, 3)

    # gold finger stubs at connector end (right = +X)  -> traces fan out
    fe = W - int(2.0 * mmx)
    for k in range(34):
        yy = 90 + k * ((H - 180) / 33)
        d.line([(fe, yy), (fe - 120 - (k % 5) * 40, yy)], fill=GOLD, width=6)

    # component footprints (x measured in mm from LEFT = mount-notch end)
    def chip(x_mm, w_mm, h_mm, label, grid):
        cx = W - x_mm * mmx
        cy = H / 2
        w = w_mm * mmx; h = h_mm * mmx
        _bga(d, cx, cy, grid[0], grid[1], min(w, h) / (max(grid) + 1), 7, GOLD)
        d.rectangle([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], outline=SILK, width=4)
        d.text((cx - w / 2, cy - h / 2 - 46), label, font=F(MONO, 40), fill=SILK)

    chip(13.5, 12, 12, "U1  PHOENIX", (14, 14))     # controller near connector
    chip(27.0, 10, 11, "U2  LPDDR4", (12, 12))      # dram
    chip(45.0, 13, 18, "U3  V-NAND", (16, 18))      # nand 1
    chip(62.0, 13, 18, "U4  V-NAND", (16, 18))      # nand 2
    # PMIC + passives rail
    px = W - 34 * mmx
    d.rectangle([px - 30, H/2 - 30, px + 30, H/2 + 30], outline=SILK, width=3)
    d.text((px - 40, H/2 + 40), "U5", font=F(MONO, 34), fill=SILK)
    rnd = 7
    for i in range(60):
        rnd = (1103515245 * rnd + 12345) & 0x7FFFFFFF
        rx = 200 + (rnd % (W - 600))
        ry = 70 + ((rnd >> 9) % (H - 140))
        d.rectangle([rx, ry, rx + 16, ry + 30], fill=GOLD)

    # fiducials
    for fx, fy in [(150, 90), (W - 150, 90), (150, H - 90)]:
        d.ellipse([fx - 14, fy - 14, fx + 14, fy + 14], fill=GOLD)

    # silk brand near connector end
    d.text((W - 11 * mmx, H - 120), "SAMSUNG  970 EVO", font=F(MONO, 40), fill=SILK)
    d.text((60, H - 120), "M.2 2280  M-KEY", font=F(MONO, 40), fill=SILK)

    # mount-notch keep-out ring at left edge
    d.arc([-40, H/2 - 130, 220, H/2 + 130], 270, 90, fill=GOLD, width=10)

    im.save(os.path.join(OUT, "tex_m2_pcb.png"))
    print("wrote tex_m2_pcb.png", im.size)


if __name__ == "__main__":
    m2_label()
    m2_label_back()
    pcb_m2()
    chip_mark("tex_ctrl_mark.png", ["SAMSUNG", "S4LR020C1", "PHOENIX", "1834  KOREA"],
              bg=(24, 24, 26), fg=(150, 150, 154))
    chip_mark("tex_nand_mark.png", ["SAMSUNG", "823", "V-NAND 3bit", "MLC  KOREA"],
              bg=(15, 15, 17), fg=(120, 120, 123))
    chip_mark("tex_dram_mark.png", ["SEC  902", "K4A8G165", "WC-BCTD"],
              bg=(15, 15, 17), fg=(120, 120, 123))
    print("done")
