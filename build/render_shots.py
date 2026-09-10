"""
Shot production for the storage-media modeling study.

    blender <model>.blend -b -P build/render_shots.py -- <mode> <outdir> [engine] [frames]

modes:  look | preview | hero | turntable | exploded | macro | wireframe

Renderer note: this workstation has no GPU, so heroes use Cycles-CPU and all
motion uses EEVEE in a fast config (no ray-tracing, low TAA) -- ~6 s/frame.
"""
import bpy, math, os, sys
sys.path.append(os.path.dirname(__file__))
import importlib, lib_common as L
importlib.reload(L)
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["preview", "prev"]
MODE = argv[0]
OUTDIR = os.path.normpath(os.path.join(L.DELIV, "renders", argv[1]))
os.makedirs(OUTDIR, exist_ok=True)

# per-mode defaults: (engine, res, samples, fast)
DEFAULTS = {
    "look":      ("BLENDER_EEVEE", (1500, 940),  16, True),
    "preview":   ("BLENDER_EEVEE", (1280, 800),  16, True),
    "hero":      ("BLENDER_EEVEE", (2200, 1375), 64, False),
    "wireframe": ("BLENDER_EEVEE", (2000, 1250), 16, True),
    "turntable": ("BLENDER_EEVEE", (1600, 1000), 16, True),
    "exploded":  ("BLENDER_EEVEE", (1600, 1000), 16, True),
    "macro":     ("BLENDER_EEVEE", (1600, 1000), 16, True),
}
ENGINE, RES, SAMPLES, FAST = DEFAULTS.get(MODE, DEFAULTS["preview"])
if len(argv) > 2 and argv[2] in ("CYCLES", "BLENDER_EEVEE"):
    ENGINE = argv[2]
FRAMES = int(argv[3]) if len(argv) > 3 and argv[3].isdigit() else None

# --------------------------------------------------------------- scene analysis
ASSET = next(o for o in bpy.data.objects if o.parent is None and o.type == 'EMPTY'
             and any(c.type == 'MESH' for c in o.children_recursive))
meshes = [o for o in ASSET.children_recursive if o.type == 'MESH']

def compute_bounds():
    global mn, mx, CENTER, SIZE, DIAG, RADIUS
    mn = Vector(( 1e9,)*3); mx = Vector((-1e9,)*3)
    for o in meshes:
        if o.hide_render:
            continue
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            for i in range(3):
                mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
    CENTER = (mn + mx) / 2
    SIZE = mx - mn
    DIAG = SIZE.length
    RADIUS = DIAG / 2

compute_bounds()

# --------------------------------------------------------------- world / lights / ground
L.studio_world(strength=0.38, top=(0.55, 0.59, 0.66), bot=(0.06, 0.06, 0.07))
L.product_light(tuple(CENTER), DIAG * 0.5)
grd = L.ground(z=mn.z - 0.02, size=DIAG * 60, color=(0.11, 0.115, 0.125), rough=0.52)

cam = L.make_camera(lens=85)
cam.data.clip_end = DIAG * 200
cam.data.clip_start = DIAG * 0.005

SCREW = next((o for o in bpy.data.objects if o.name == "MountScrew"), None)

def set_screw_visible(v):
    if SCREW:
        for o in [SCREW] + list(SCREW.children_recursive):
            o.hide_render = not v
    compute_bounds()

def cfg(exposure=0.35):
    L.render_cfg(engine=ENGINE, samples=SAMPLES, res=RES, exposure=exposure,
                 look='AgX - Medium Contrast', fast=FAST)

def visible_corners(xband=None):
    pts = []
    for o in meshes:
        if o.hide_render:
            continue
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            if xband and not (xband[0] <= w.x <= xband[1]):
                continue
            pts.append(w)
    return pts or [CENTER]

def aim_dir(az, el):
    a, e = math.radians(az), math.radians(el)
    return Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e)))

def place_fit(target, az, el, margin=1.10, pts=None, lens=None, roll=0.0):
    """Position cam by fitting the projected bbox corners to the frame."""
    if lens:
        cam.data.lens = lens
    t = Vector(target)
    d = aim_dir(az, el)
    pts = pts if pts is not None else visible_corners()
    tan_h = math.tan(cam.data.angle / 2.0)              # angle is along the long axis (width)
    tan_v = tan_h * RES[1] / RES[0]
    dist = max(SIZE) * 3.0
    for _ in range(5):
        cam.location = t + d * dist
        L.look_at(cam, t + Vector((0, 0, max(SIZE) * roll)))
        bpy.context.view_layer.update()
        inv = cam.matrix_world.inverted()
        mu = mv = 1e-6
        for p in pts:
            cp = inv @ p
            if cp.z >= -1e-4:
                continue
            mu = max(mu, abs(cp.x) / -cp.z)
            mv = max(mv, abs(cp.y) / -cp.z)
        dist *= max(mu / tan_h, mv / tan_v) * margin
    cam.location = t + d * dist
    L.look_at(cam, t + Vector((0, 0, max(SIZE) * roll)))
    bpy.context.view_layer.update()

def shot(name, az, el, margin=1.08, tgt=None, pts=None, lens=None, roll=0.0, exposure=0.35):
    place_fit(CENTER if tgt is None else tgt, az, el, margin, pts, lens, roll)
    cfg(exposure)
    L.render_to(os.path.join(OUTDIR, f"{name}.png"))

# --------------------------------------------------------------- exploded rig
TIERS = {
    "MountScrew": -2, "Screw_": -2,
    "PCB": 0, "MountRing": 0, "Fingers": 0, "PMIC": 1, "U5_": 1,
    "U1_": 2, "U2_": 2, "U3_": 3, "U4_": 3,
    "PottingFill": 4, "CopperFilm": 5, "Label": 6,
    "BottomPlate": -3, "BackLabel": -4,
    "IntPCB": 0, "SATA_": 0,
    "U100": 1, "U200": 1, "sp": 1, "U300": 2, "U301": 2,
    "ThermalPad": 3, "TopShell": 4, "FrontLabel": 6,
}
def tier_of(o):
    for k, v in TIERS.items():
        if k in o.name:
            return v
    if o.name[:1] in ("C", "R") and o.name[1:3].isdigit():
        return 1
    return 2

_HOME = {o.name: o.location.copy() for o in ASSET.children_recursive if o.type in ('MESH', 'EMPTY')}
_TV = sorted({tier_of(o) for o in ASSET.children_recursive if o.name in _HOME})
_STEP = max(SIZE.z, 2.0) * 3.0

def set_explode(f):
    for o in ASSET.children_recursive:
        if o.name in _HOME:
            h = _HOME[o.name]
            o.location = (h.x, h.y, h.z + tier_of(o) * _STEP * f)

def explode_span(f):
    return min(_TV) * _STEP * f + mn.z, max(_TV) * _STEP * f + mx.z

# --------------------------------------------------------------- modes
CONN_HI = mx.x                       # connector end
NOTCH_LO = mn.x                      # mount-notch end
conn_pts  = lambda: visible_corners(xband=(CONN_HI - 22, CONN_HI + 3))
notch_pts = lambda: visible_corners(xband=(NOTCH_LO - 3, NOTCH_LO + 20))

if MODE in ("look", "preview"):
    set_screw_visible(False)
    shot("L1", -43, 33, margin=1.06, lens=85)
    shot("L2_top", -90, 82, margin=1.03, lens=95)
    shot("L3_conn", 30, 20, margin=1.12, tgt=(CONN_HI - 9, 0, CENTER.z), pts=conn_pts(), lens=70)
    shot("L4_notch", 150, 24, margin=1.12, tgt=(NOTCH_LO + 8, 0, CENTER.z), pts=notch_pts(), lens=70)
    set_screw_visible(True); set_explode(1.0)
    lo, hi = explode_span(1.0)
    tgt = (CENTER.x, CENTER.y, (lo + hi) / 2)
    place_fit(tgt, -52, 26, margin=1.08, lens=80)
    cfg(); L.render_to(os.path.join(OUTDIR, "L5_explode.png"))

elif MODE == "hero":
    set_screw_visible(False)
    shot("hero_01", -43, 33, margin=1.05, lens=85)
    shot("hero_02", -26, 22, margin=1.06, lens=80)
    shot("hero_03_conn", 32, 21, margin=1.12, tgt=(CONN_HI - 9, 0, CENTER.z),
         pts=conn_pts(), lens=65)
    shot("hero_04_top", -90, 80, margin=1.03, lens=95)
    shot("hero_05_notch", 150, 25, margin=1.12, tgt=(NOTCH_LO + 8, 0, CENTER.z),
         pts=notch_pts(), lens=65)

elif MODE == "wireframe":
    set_screw_visible(False)
    clay = L.mat_solid("clay", (0.62, 0.62, 0.64), rough=0.62)
    ink = L.mat_solid("wire_ink", (0.03, 0.03, 0.035), rough=0.7)
    for o in meshes:
        o.data.materials.clear(); o.data.materials.append(clay); o.data.materials.append(ink)
        m = o.modifiers.new("wf", 'WIREFRAME'); m.thickness = 0.05
        m.use_replace = False; m.material_offset = 1
    shot("wire_01", -43, 33, margin=1.05, lens=85)
    shot("wire_02_top", -90, 80, margin=1.03, lens=95)
    shot("wire_03_conn", 32, 21, margin=1.12, tgt=(CONN_HI - 9, 0, CENTER.z),
         pts=conn_pts(), lens=65)

elif MODE == "exploded":
    set_screw_visible(True)
    frames = FRAMES or 60
    for i in range(frames):
        f = i / (frames - 1)
        ease = 0.5 - 0.5 * math.cos(f * math.pi)
        set_explode(ease)
        lo, hi = explode_span(ease)
        tgt = (CENTER.x, CENTER.y, (lo + hi) / 2)
        place_fit(tgt, -58 + 26 * f, 20 + 12 * ease, margin=1.14, lens=80)
        cfg()
        L.render_to(os.path.join(OUTDIR, f"f{i:03d}.png"))

elif MODE == "turntable":
    set_screw_visible(False)
    frames = FRAMES or 72
    cam.data.lens = 72
    # lock one distance fitted to the widest (side-on) presentation, then just orbit
    place_fit(CENTER, -90, 24, margin=1.07, lens=72)
    fixed = (cam.location - CENTER).length
    for i in range(frames):
        az = -180 + 360 * i / frames
        cam.location = CENTER + aim_dir(az, 24) * fixed
        L.look_at(cam, CENTER)
        cfg()
        L.render_to(os.path.join(OUTDIR, f"f{i:03d}.png"))

elif MODE == "macro":
    # crawl low along the bare PCB, past the real semiconductor packages
    set_screw_visible(False)
    for nm in ("Label", "CopperFilm", "PottingFill"):
        for o in meshes:
            if nm in o.name:
                o.hide_render = True
    compute_bounds()
    frames = FRAMES or 54
    cam.data.lens = 50
    cam.data.dof.use_dof = True
    cam.data.dof.aperture_fstop = 3.5
    for i in range(frames):
        f = i / (frames - 1)
        ease = 0.5 - 0.5 * math.cos(f * math.pi)
        x = mn.x + SIZE.x * (0.06 + 0.86 * ease)
        cam.location = Vector((x - SIZE.x * 0.06, CENTER.y - SIZE.y * 1.5, mn.z + SIZE.z * 3.0))
        tgt = Vector((x + SIZE.x * 0.12, CENTER.y + SIZE.y * 0.15, CENTER.z + SIZE.z * 0.6))
        L.look_at(cam, tgt)
        cam.data.dof.focus_distance = (cam.location - tgt).length
        cfg(exposure=0.6)
        L.render_to(os.path.join(OUTDIR, f"f{i:03d}.png"))

print("DONE", MODE, ENGINE, RES)
