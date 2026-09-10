"""
Inline every {{IMG:name}} / {{POSTER:name}} / {{VID:name}} placeholder in
portfolio_src.html as a data URI and write deliverables/portfolio.html.

    python build/pack_portfolio.py
"""
import base64, io, os, re, sys
from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "build", "portfolio_src.html")
OUT = os.path.join(ROOT, "deliverables", "portfolio.html")
R = os.path.join(ROOT, "deliverables", "renders")
V = os.path.join(ROOT, "deliverables", "video")
T = os.path.join(ROOT, "refs", "textures")

# name -> (path, kind)  kind: img | poster | vid
ASSETS = {
    "hero":            (f"{R}/m2_hero/hero_01.png", "img"),
    "hero_wire":       (f"{R}/m2_wire/wire_01.png", "img"),
    "conn":            (f"{R}/m2_hero/hero_03_conn.png", "img"),
    "top":             (f"{R}/m2_hero/hero_04_top.png", "img"),
    "notch":           (f"{R}/m2_hero/hero_05_notch.png", "img"),
    "label_art":       (f"{T}/tex_m2_label.png", "img"),
    "pcb_art":         (f"{T}/tex_m2_pcb.png", "img"),
    "macro_poster":    (f"{V}/m2_macro_poster.png", "poster"),
    "exploded_poster": (f"{V}/m2_exploded_poster.png", "poster"),
    "turntable_poster":(f"{V}/m2_turntable_poster.png", "poster"),
    "macro":           (f"{V}/m2_macro_web.mp4", "vid"),
    "exploded":        (f"{V}/m2_exploded_web.mp4", "vid"),
    "turntable":       (f"{V}/m2_turntable_web.mp4", "vid"),
}
MAXW = {"img": 1800, "poster": 1280}
QUAL = {"img": 88, "poster": 80}
WIDE_IMG = {"label_art": 2000, "pcb_art": 2000}


def jpeg_uri(path, kind, name):
    im = Image.open(path).convert("RGB")
    mw = WIDE_IMG.get(name, MAXW[kind])
    if im.width > mw:
        im = im.resize((mw, round(im.height * mw / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=QUAL[kind], optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode(), len(buf.getvalue())


def vid_uri(path):
    data = open(path, "rb").read()
    return "data:video/mp4;base64," + base64.b64encode(data).decode(), len(data)


def gltf_tris():
    """Sum triangle count from the exported GLB (index accessor counts / 3)."""
    import json, struct
    p = os.path.join(ROOT, "deliverables", "models", "m2_970evo.glb")
    if not os.path.exists(p):
        return "13k"
    b = open(p, "rb").read()
    jlen = struct.unpack("<I", b[12:16])[0]
    j = json.loads(b[20:20 + jlen])
    tris = 0
    for m in j.get("meshes", []):
        for pr in m["primitives"]:
            if "indices" in pr:
                tris += j["accessors"][pr["indices"]]["count"] // 3
            else:
                tris += j["accessors"][pr["attributes"]["POSITION"]]["count"] // 3
    return f"{tris/1000:.1f}k" if tris >= 1000 else str(tris)


def main():
    html = open(SRC, encoding="utf-8").read()
    html = html.replace("{{TRIS}}", gltf_tris())
    total = 0
    missing = []
    for name, (path, kind) in ASSETS.items():
        tokens = [f"{{{{IMG:{name}}}}}", f"{{{{POSTER:{name}}}}}", f"{{{{VID:{name}}}}}"]
        if not any(t in html for t in tokens):
            continue
        if not os.path.exists(path):
            missing.append(f"{name} -> {path}")
            continue
        if kind == "vid":
            uri, n = vid_uri(path)
        else:
            uri, n = jpeg_uri(path, kind, name)
        total += n
        for t in tokens:
            html = html.replace(t, uri)
        print(f"  {name:18s} {kind:7s} {n/1024:8.1f} KB")
    leftovers = re.findall(r"\{\{(IMG|POSTER|VID):([a-z_]+)\}\}", html)
    if leftovers:
        print("!! unresolved placeholders:", leftovers)
    if missing:
        print("!! missing files:\n   " + "\n   ".join(missing))
    open(OUT, "w", encoding="utf-8").write(html)
    print(f"\nwrote {OUT}   payload {total/1024/1024:.2f} MB   file {os.path.getsize(OUT)/1024/1024:.2f} MB")
    if os.path.getsize(OUT) > 15_500_000:
        print("!! OVER 15.5 MB - reduce quality/resolution")
        sys.exit(1)


main()
