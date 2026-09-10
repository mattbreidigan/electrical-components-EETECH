"""Diagnostic clay renders of the M.2 model - expose modeling defects.
   blender deliverables/models/m2_970evo.blend -b -P build/diag_m2.py
"""
import bpy, math, os, sys
sys.path.append(os.path.dirname(__file__))
import lib_common as L
from mathutils import Vector

OUT = os.path.normpath(os.path.join(L.DELIV, "renders", "m2_diag"))
os.makedirs(OUT, exist_ok=True)

ASSET = next(o for o in bpy.data.objects if o.parent is None and o.type == 'EMPTY'
             and any(c.type == 'MESH' for c in o.children_recursive))
meshes = [o for o in ASSET.children_recursive if o.type == 'MESH']

# neutral clay on everything, but tint a few parts so we can tell them apart
clay = L.mat_solid("clay", (0.62, 0.62, 0.63), rough=0.5)
tints = {
    "Label": (0.80, 0.30, 0.25), "CopperFilm": (0.85, 0.55, 0.25),
    "PCB": (0.25, 0.45, 0.30), "Fingers": (0.85, 0.72, 0.30),
    "U1_": (0.30, 0.45, 0.75), "U2_": (0.35, 0.55, 0.80),
    "U3_": (0.45, 0.40, 0.72), "U4_": (0.50, 0.45, 0.78),
    "Screw": (0.7, 0.7, 0.72),
}
for o in meshes:
    m = clay
    for k, c in tints.items():
        if k in o.name:
            m = L.mat_solid("t_" + o.name, c, rough=0.5); break
    o.data.materials.clear(); o.data.materials.append(m)
    o.hide_render = False   # show screw too

mn = Vector((1e9,)*3); mx = Vector((-1e9,)*3)
for o in meshes:
    for c in o.bound_box:
        w = o.matrix_world @ Vector(c)
        for i in range(3):
            mn[i] = min(mn[i], w[i]); mx[i] = max(mx[i], w[i])
C = (mn + mx) / 2; S = mx - mn

L.studio_world(strength=0.7, top=(0.8, 0.82, 0.86), bot=(0.2, 0.2, 0.22))
L.area_light("k", (C.x + 60, C.y - 80, C.z + 120), tuple(C), 4e5, 120)
L.area_light("f", (C.x - 90, C.y - 40, C.z + 40), tuple(C), 1.2e5, 160)
L.ground(z=mn.z - 0.02, size=4000, color=(0.15, 0.15, 0.16), rough=0.6)
cam = L.make_camera(lens=60); cam.data.clip_end = 5000

def cfg():
    L.render_cfg(engine='BLENDER_EEVEE', samples=24, res=(1600, 1000),
                 exposure=0.0, look='AgX - Base Contrast', fast=True)

def look_at(t):
    d = Vector(t) - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

def shot(name, loc, tgt, ortho=None):
    cam.location = Vector(loc)
    if ortho:
        cam.data.type = 'ORTHO'; cam.data.ortho_scale = ortho
    else:
        cam.data.type = 'PERSP'
    look_at(tgt)
    cfg()
    bpy.context.scene.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("wrote", name)

connx = mx.x  # connector end
notchx = mn.x

# 1 side elevation of connector end (see finger + label gaps)
shot("01_conn_side", (connx + 3, C.y - 60, C.z + 6), (connx - 6, C.y, C.z), ortho=26)
# 2 side elevation of notch end
shot("02_notch_side", (notchx - 3, C.y - 60, C.z + 6), (notchx + 8, C.y, C.z), ortho=26)
# 3 long side elevation (whole module, label/pcb/chip stack)
shot("03_long_side", (C.x, C.y - 200, C.z + 4), (C.x, C.y, C.z), ortho=90)
# 4 3/4 connector closeup
shot("04_conn_iso", (connx + 22, C.y - 24, C.z + 20), (connx - 4, C.y, C.z))
# 5 3/4 notch closeup
shot("05_notch_iso", (notchx - 20, C.y - 22, C.z + 18), (notchx + 6, C.y, C.z))
# 6 top ortho
shot("06_top", (C.x, C.y, C.z + 200), (C.x, C.y, C.z), ortho=88)
# 7 bottom ortho
shot("07_bottom", (C.x, C.y, mn.z - 200), (C.x, C.y, C.z), ortho=88)
# 8 underside 3/4 (fingers on back face, chip pins)
shot("08_under_iso", (C.x + 30, C.y - 40, mn.z - 30), (C.x, C.y, C.z))
print("DIAG DONE", "bounds", tuple(round(v,3) for v in S))
