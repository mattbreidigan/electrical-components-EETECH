"""
Samsung 970 EVO  -  M.2 2280 NVMe SSD  (500 GB), modeling study.
Real-world mm.  Origin: centre of the semicircular mount notch, PCB mid-plane.
+X -> connector end,  +Z -> label side.

    blender -b -P build/model_m2.py
"""
import bpy, bmesh, math, os, sys
sys.path.append(os.path.dirname(__file__))
import importlib, lib_common as L
importlib.reload(L)

MODELS = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "deliverables", "models"))
os.makedirs(MODELS, exist_ok=True)

# ---- datasheet dims (mm) -----------------------------------------------------
LEN, WID, TPCB = 80.15, 22.15, 0.80
CONN_X = LEN / 2                 # +X edge (connector)
NOTCH_X = -LEN / 2               # -X edge (mount notch)
CORNER_R = 0.60
PCB_TOP = TPCB / 2
KEY_W, KEY_D = 1.20, 3.40        # M-key notch (width along Y, depth into board)
KEY_Y = 5.10                     # notch centre in Y  -> short pad block on +Y side
MOUNT_R = 1.90

CH_NAND, CH_DRAM, CH_CTRL, CH_PMIC = 1.05, 0.95, 0.95, 0.72
TOP_CHIP = PCB_TOP + CH_NAND     # 1.45 : height of the tallest package

L.reset()
sc = bpy.context.scene
root = bpy.data.objects.new("M2_970EVO", None)
sc.collection.objects.link(root)
root.empty_display_size = 6
IC_OBJS = []

def parent(o, p=root):
    o.parent = p
    return o

def finalize(o, smooth=35):
    L.apply_all(o)
    L.shade_smooth(o, smooth)
    return o

def planar_uv_top(obj):
    me = obj.data
    xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    w, d = maxx - minx, maxy - miny
    uvl = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    for loop in me.loops:
        co = me.vertices[loop.vertex_index].co
        uvl.data[loop.index].uv = ((co.x - minx) / w, (co.y - miny) / d)


# ---------------------------------------------------------------- PCB
def build_pcb():
    o = L.rounded_rect_prism("PCB", LEN, WID, TPCB, CORNER_R, loc=(0, 0, 0), fillet=0.07)
    finalize(o, 40)
    key = L.cube("key_cut", (KEY_D * 2, KEY_W, 4), loc=(CONN_X, KEY_Y, 0))
    L.boolean(o, key)
    bpy.ops.mesh.primitive_cylinder_add(radius=MOUNT_R, depth=6, location=(NOTCH_X, 0, 0), vertices=56)
    L.boolean(o, bpy.context.active_object)
    L.shade_smooth(o, 40)
    planar_uv_top(o)
    L.assign(o, L.mat_pcb("pcb_m2", tex_name="tex_m2_pcb.png"))
    parent(o)

    # bare-copper keep-out ring around the mount notch, built as a half-annulus (bmesh)
    gold = L.mat_gold_contact("keepout_gold")
    for z in (PCB_TOP + 0.010, -PCB_TOP - 0.010):
        bm = bmesh.new()
        ri, ro = MOUNT_R + 0.15, MOUNT_R + 1.35
        segs = 28
        ring_v = []
        for i in range(segs + 1):
            a = -math.pi / 2 + math.pi * i / segs      # -90deg .. +90deg (board side)
            ci, co = (math.cos(a), math.sin(a)), None
            vi = bm.verts.new((NOTCH_X + ri * math.cos(a), ri * math.sin(a), 0))
            vo = bm.verts.new((NOTCH_X + ro * math.cos(a), ro * math.sin(a), 0))
            ring_v.append((vi, vo))
        for i in range(segs):
            bm.faces.new((ring_v[i][0], ring_v[i][1], ring_v[i + 1][1], ring_v[i + 1][0]))
        bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.05)
        me = bpy.data.meshes.new("MountRing"); bm.to_mesh(me); bm.free()
        ring = bpy.data.objects.new("MountRing", me); sc.collection.objects.link(ring)
        ring.location.z = z
        L.shade_smooth(ring, 40); L.assign(ring, gold); parent(ring)
    return o


# ---------------------------------------------------------------- gold edge fingers
def finger_block(name, y0, count, pitch=0.50, fw=0.28, reach=3.9):
    grp = bpy.data.objects.new(name, None); sc.collection.objects.link(grp); parent(grp)
    for face, z in (("T", PCB_TOP + 0.012), ("B", -PCB_TOP - 0.012)):
        base = L.cube(f"{name}_{face}", (reach, fw, 0.035), loc=(CONN_X - reach / 2, y0, z))
        m = base.modifiers.new("arr", 'ARRAY'); m.count = count
        m.use_relative_offset = False; m.use_constant_offset = True
        m.constant_offset_displace = (0, pitch, 0)
        L.bevel(base, width=0.025, segments=2, angle=40)
        finalize(base, 40)
        L.assign(base, gold)
        base.parent = grp
    return grp


def build_fingers():
    global gold
    gold = L.mat_gold_contact()
    # short block on +Y side of the key, long block filling the rest
    short_y0 = KEY_Y + KEY_W / 2 + 0.40
    n_short = int((WID / 2 - 1.0 - short_y0) / 0.5) + 1
    finger_block("Fingers_short", short_y0, max(n_short, 7))
    long_y0 = -WID / 2 + 1.05
    n_long = int((KEY_Y - KEY_W / 2 - 0.40 - long_y0) / 0.5) + 1
    finger_block("Fingers_long", long_y0, max(n_long, 26))


# ---------------------------------------------------------------- components
def ic(name, x_mm_from_conn, w, d, h, mat):
    cx = CONN_X - x_mm_from_conn
    o = L.cube(name, (w, d, h), loc=(cx, 0, PCB_TOP + h / 2))
    L.bevel(o, width=min(0.09, h * 0.16), segments=2, angle=40)
    finalize(o, 40)
    L.box_uv_project(o)
    L.assign(o, mat)
    IC_OBJS.append(o)
    return parent(o)


def passive(name, x, y, w=0.5, d=1.0, h=0.45):
    o = L.cube(name, (w, d, h), loc=(x, y, PCB_TOP + h / 2))
    L.bevel(o, width=0.04, segments=1, angle=40)
    finalize(o, 40)
    L.assign(o, pass_mat)
    return parent(o)


def build_components():
    global pass_mat
    ctrl_mat = L.mat_ic("ic_phoenix", mark_tex="tex_ctrl_mark.png", tint=(0.11, 0.11, 0.12),
                        rough=0.30, metal=0.7)
    dram_mat = L.mat_ic("ic_dram", mark_tex="tex_dram_mark.png", rough=0.46)
    nand_mat = L.mat_ic("ic_nand", mark_tex="tex_nand_mark.png", rough=0.52)
    pmic_mat = L.mat_ic("ic_pmic", tint=(0.03, 0.03, 0.035), rough=0.4)
    pass_mat = L.mat_solid("passive", (0.14, 0.12, 0.10), rough=0.5)

    ic("U1_Phoenix", 14.0, 12.0, 12.0, CH_CTRL, ctrl_mat)
    ic("U2_LPDDR4", 28.0, 10.0, 11.0, CH_DRAM, dram_mat)
    ic("U3_VNAND", 45.5, 13.0, 18.0, CH_NAND, nand_mat)
    ic("U4_VNAND", 62.0, 13.0, 18.0, CH_NAND, nand_mat)
    ic("U5_PMIC", 35.5, 3.2, 3.2, CH_PMIC, pmic_mat)

    xs = [CONN_X - v for v in (10, 21, 23, 37, 39, 55, 57, 71, 73)]
    for i, x in enumerate(xs):
        y = (WID / 2 - 1.7) * (1 if i % 2 else -1)
        passive(f"C{i:02d}", x, y)
        passive(f"R{i:02d}", x, y * 0.55, w=0.4, d=0.8, h=0.35)
    # low SMD parts on the exposed PCB near the connector edge
    for i, x in enumerate((CONN_X - 5.4, CONN_X - 6.6)):
        for j, y in enumerate((-8.0, -4.0, 0.0, 4.0, 8.0)):
            passive(f"Cc{i}{j}", x, y, w=0.32, d=0.62, h=0.22)


# ---------------------------------------------------------------- potting + film + label
def build_stack():
    lab_w, lab_d = LEN - 7.0, WID - 0.9
    pot_w, pot_d = LEN - 7.6, WID - 1.5
    z_bot = PCB_TOP - 0.02
    pot_h = TOP_CHIP + 0.02 - z_bot

    # gap-filler: a matte slab that spans PCB-top -> chip-top, with the chip
    # footprints cut out so the packages stay put in the exploded view.
    pot = L.rounded_rect_prism("PottingFill", pot_w, pot_d, pot_h, CORNER_R,
                               loc=(-1.4, 0, z_bot + pot_h / 2), fillet=0.03)
    finalize(pot, 30)
    for chip in IC_OBJS:
        bb = chip.dimensions
        cut = L.cube("potcut", (bb.x + 0.35, bb.y + 0.35, pot_h + 1.0),
                     loc=(chip.location.x, chip.location.y, z_bot + pot_h / 2))
        L.boolean(pot, cut)
    finalize(pot, 30)
    L.assign(pot, L.mat_solid("potting", (0.020, 0.020, 0.023), rough=0.55))
    parent(pot)

    cu = L.rounded_rect_prism("CopperFilm", pot_w, pot_d, 0.05, CORNER_R,
                              loc=(-1.4, 0, TOP_CHIP + 0.055), fillet=0.02)
    finalize(cu, 40); planar_uv_top(cu)
    L.assign(cu, L.mat_solid("copper_film", (0.44, 0.28, 0.17), rough=0.52, metal=1.0))
    parent(cu)

    lab = L.rounded_rect_prism("Label", lab_w, lab_d, 0.13, CORNER_R,
                               loc=(-1.4, 0, TOP_CHIP + 0.135), fillet=0.03)
    finalize(lab, 40); planar_uv_top(lab)
    L.assign(lab, L.mat_label("label_m2", "tex_m2_label.png"))
    parent(lab)


# ---------------------------------------------------------------- mounting screw
def build_screw():
    grp = bpy.data.objects.new("MountScrew", None); sc.collection.objects.link(grp); parent(grp)
    steel = L.mat_steel("screw_steel")
    cx = NOTCH_X + 0.9
    HEAD_H = 0.70
    bpy.ops.mesh.primitive_cylinder_add(radius=1.55, depth=HEAD_H, vertices=40,
                                        location=(cx, 0, PCB_TOP + HEAD_H / 2))
    head = bpy.context.active_object; head.name = "Screw_head"
    L.bevel(head, width=0.09, segments=2, angle=35)
    for ang in (0, 90):
        c = L.cube(f"ph{ang}", (2.1, 0.26, 0.30),
                   loc=(cx, 0, PCB_TOP + HEAD_H - 0.02))
        c.rotation_euler = (0, 0, math.radians(ang))
        L.boolean(head, c)
    finalize(head, 35); L.assign(head, steel); head.parent = grp
    bpy.ops.mesh.primitive_cylinder_add(radius=0.80, depth=2.0, vertices=28,
                                        location=(cx, 0, PCB_TOP - 1.0))
    shft = bpy.context.active_object; shft.name = "Screw_shaft"
    finalize(shft, 30); L.assign(shft, steel); shft.parent = grp


# ---------------------------------------------------------------- assemble
build_pcb()
build_fingers()
build_components()
build_stack()
build_screw()

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(MODELS, "m2_970evo.blend"))
tri = sum(len(o.data.polygons) for o in bpy.data.objects if o.type == 'MESH')
mnb = [1e9]*3; mxb = [-1e9]*3
for o in bpy.data.objects:
    if o.type == 'MESH' and 'Screw' not in o.name and 'MountScrew' not in o.name:
        for c in o.bound_box:
            from mathutils import Vector
            w = o.matrix_world @ Vector(c)
            for i in range(3):
                mnb[i] = min(mnb[i], w[i]); mxb[i] = max(mxb[i], w[i])
print("SAVED", os.path.join(MODELS, "m2_970evo.blend"))
print("mesh objects:", len([o for o in bpy.data.objects if o.type == 'MESH']), " faces:", tri)
print("bbox (no screw):", [round(mxb[i]-mnb[i], 3) for i in range(3)])
