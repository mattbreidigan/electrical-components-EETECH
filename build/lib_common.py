"""
Shared Blender helpers for the storage-media modeling study.
Blender 5.1 / EEVEE + Cycles.  All units millimetres.
"""
import bpy, bmesh, math, os
from mathutils import Vector

TEX = os.path.join(os.path.dirname(__file__), "..", "refs", "textures")
DELIV = os.path.join(os.path.dirname(__file__), "..", "deliverables")


# --------------------------------------------------------------------------- scene
def reset(unit_scale=0.001):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    sc.unit_settings.scale_length = unit_scale        # 1 BU = 1 mm
    sc.unit_settings.length_unit = 'MILLIMETERS'
    return sc


def _img(name):
    path = os.path.normpath(os.path.join(TEX, name))
    if name in bpy.data.images:
        return bpy.data.images[name]
    im = bpy.data.images.load(path)
    im.name = name
    return im


# --------------------------------------------------------------------------- materials
def _new(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    out.location = (400, 0); bsdf.location = (0, 0)
    return m, nt, bsdf


def _set(b, **kw):
    for k, v in kw.items():
        if k in b.inputs:
            b.inputs[k].default_value = v


def mat_solid(name, color, rough=0.5, metal=0.0, spec=0.5, coat=0.0):
    m, nt, b = _new(name)
    _set(b, **{"Base Color": (*color, 1), "Roughness": rough, "Metallic": metal})
    if "Specular IOR Level" in b.inputs:
        b.inputs["Specular IOR Level"].default_value = spec
    if coat and "Coat Weight" in b.inputs:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = 0.08
    return m


def mat_anodized_alu(name="alu_anodized", color=(0.052, 0.053, 0.057)):
    """Dark grey bead-blasted anodised aluminium (860 EVO shell)."""
    m, nt, b = _new(name)
    _set(b, **{"Base Color": (*color, 1), "Metallic": 1.0, "Roughness": 0.46})
    # fine blast speckle -> roughness + micro-normal
    tex = nt.nodes.new("ShaderNodeTexNoise"); tex.location = (-760, -220)
    tex.inputs["Scale"].default_value = 1400.0
    tex.inputs["Detail"].default_value = 4.0
    tex.inputs["Roughness"].default_value = 0.85
    rr = nt.nodes.new("ShaderNodeMath"); rr.location = (-460, -140)
    rr.operation = 'MULTIPLY_ADD'; rr.inputs[1].default_value = 0.14; rr.inputs[2].default_value = 0.42
    nt.links.new(tex.outputs["Fac"], rr.inputs[0])
    nt.links.new(rr.outputs[0], b.inputs["Roughness"])
    bump = nt.nodes.new("ShaderNodeBump"); bump.location = (-460, -340)
    bump.inputs["Strength"].default_value = 0.14
    bump.inputs["Distance"].default_value = 0.0015
    nt.links.new(tex.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def mat_gold_contact(name="gold_contact"):
    m, nt, b = _new(name)
    _set(b, **{"Base Color": (0.94, 0.72, 0.30, 1), "Metallic": 1.0, "Roughness": 0.22})
    return m


def mat_pcb(name, tex_name=None, base=(0.015, 0.016, 0.018), rough=0.58):
    """Black solder-mask PCB (matte-satin).  Optional baked artwork (silk + pads)."""
    m, nt, b = _new(name)
    _set(b, **{"Base Color": (*base, 1), "Roughness": rough, "Metallic": 0.0})
    if "Specular IOR Level" in b.inputs:
        b.inputs["Specular IOR Level"].default_value = 0.35
    if tex_name:
        t = nt.nodes.new("ShaderNodeTexImage"); t.location = (-520, 60)
        t.image = _img(tex_name)
        t.image.colorspace_settings.name = 'sRGB'
        nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
        # use texture luminance as a light roughness break-up
        rr = nt.nodes.new("ShaderNodeMath"); rr.location = (-260, -200); rr.operation = 'MULTIPLY_ADD'
        rr.inputs[1].default_value = -0.18; rr.inputs[2].default_value = rough
        nt.links.new(t.outputs["Color"], rr.inputs[0])
        nt.links.new(rr.outputs[0], b.inputs["Roughness"])
        bump = nt.nodes.new("ShaderNodeBump"); bump.location = (-260, -420)
        bump.inputs["Strength"].default_value = 0.15
        bump.inputs["Distance"].default_value = 0.002
        nt.links.new(t.outputs["Color"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def mat_ic(name, mark_tex=None, tint=(0.02, 0.02, 0.022), rough=0.5, metal=0.0):
    """Black epoxy IC package with optional laser-etch top mark."""
    m, nt, b = _new(name)
    _set(b, **{"Base Color": (*tint, 1), "Roughness": rough, "Metallic": metal})
    if mark_tex:
        t = nt.nodes.new("ShaderNodeTexImage"); t.location = (-520, 40)
        t.image = _img(mark_tex); t.projection = 'FLAT'
        t.image.colorspace_settings.name = 'sRGB'
        nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
        bump = nt.nodes.new("ShaderNodeBump"); bump.location = (-260, -260)
        bump.inputs["Strength"].default_value = 0.25
        bump.inputs["Distance"].default_value = 0.004
        nt.links.new(t.outputs["Color"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
        # generated box UV so the mark maps to the top face
    return m


def mat_nickel(name="nickel_lid"):
    m, nt, b = _new(name)
    _set(b, **{"Base Color": (0.62, 0.63, 0.64, 1), "Metallic": 1.0, "Roughness": 0.28})
    return m


def mat_label(name, tex_name, rough=0.90, coat=0.0):
    """Near-Lambertian printed paper label: minimal spec, very high roughness."""
    m, nt, b = _new(name)
    t = nt.nodes.new("ShaderNodeTexImage"); t.location = (-720, 60)
    t.image = _img(tex_name)
    t.image.colorspace_settings.name = 'sRGB'
    cc = nt.nodes.new("ShaderNodeBrightContrast"); cc.location = (-380, 60)
    cc.inputs["Bright"].default_value = 0.020
    nt.links.new(t.outputs["Color"], cc.inputs["Color"])
    nt.links.new(cc.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    n = nt.nodes.new("ShaderNodeTexNoise"); n.location = (-620, -260)
    n.inputs["Scale"].default_value = 520.0
    n.inputs["Detail"].default_value = 2.0
    bump = nt.nodes.new("ShaderNodeBump"); bump.location = (-360, -300)
    bump.inputs["Strength"].default_value = 0.025
    nt.links.new(n.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    if "Specular IOR Level" in b.inputs:
        b.inputs["Specular IOR Level"].default_value = 0.13
    return m


def mat_solder(name="solder"):
    return mat_solid(name, (0.55, 0.55, 0.57), rough=0.30, metal=1.0)


def mat_thermal_pad(name="thermal_pad"):
    return mat_solid(name, (0.28, 0.29, 0.33), rough=0.85)


def mat_steel(name="steel"):
    return mat_solid(name, (0.52, 0.53, 0.55), rough=0.34, metal=1.0)


def assign(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj


# --------------------------------------------------------------------------- geo helpers
def cube(name, size, loc=(0, 0, 0), parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    if parent:
        o.parent = parent
    return o


def _mset(m, **kw):
    for k, v in kw.items():
        if hasattr(m, k):
            setattr(m, k, v)


def bevel(obj, width=0.15, segments=3, angle=40, clamp=True, harden=True):
    m = obj.modifiers.new("bevel", 'BEVEL')
    m.width = width
    m.segments = segments
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(angle)
    _mset(m, use_clamp_overlap=clamp, harden_normals=harden, use_harden_normals=harden)
    return obj


def apply_all(obj):
    prev = bpy.context.view_layer.objects.active
    bpy.context.view_layer.objects.active = obj
    for mo in list(obj.modifiers):
        try:
            bpy.ops.object.modifier_apply(modifier=mo.name)
        except Exception as e:
            print("apply fail", obj.name, mo.name, e)
    bpy.context.view_layer.objects.active = prev
    return obj


def shade_smooth(obj, angle=30):
    """Smooth shading with an angle split (Blender 4.1+ removed mesh.use_auto_smooth)."""
    for p in obj.data.polygons:
        p.use_smooth = True
    prev_act = bpy.context.view_layer.objects.active
    bpy.context.view_layer.objects.active = obj
    for opname in ("shade_smooth_by_angle", "shade_auto_smooth"):
        op = getattr(bpy.ops.object, opname, None)
        if op is None:
            continue
        try:
            op(angle=math.radians(angle)); break
        except TypeError:
            try:
                op(use_auto_smooth=True, angle=math.radians(angle)); break
            except Exception:
                pass
        except Exception:
            pass
    bpy.context.view_layer.objects.active = prev_act


def solidify(obj, thickness):
    m = obj.modifiers.new("solid", 'SOLIDIFY')
    m.thickness = thickness
    m.offset = 0
    return obj


def rounded_rect_prism(name, w, d, h, r, loc=(0, 0, 0), fillet=0.0, seg=6):
    """Box with rounded vertical corners (radius r).  Optional top/bottom fillet via bevel."""
    bm = bmesh.new()
    # build rounded rect outline (XY), centred
    pts = []
    cx = w / 2 - r
    cy = d / 2 - r
    corners = [(cx, cy, 0), (-cx, cy, math.pi / 2), (-cx, -cy, math.pi), (cx, -cy, 3 * math.pi / 2)]
    for ox, oy, a0 in corners:
        for i in range(seg + 1):
            a = a0 + (math.pi / 2) * (i / seg)
            pts.append((ox + r * math.cos(a), oy + r * math.sin(a)))
    verts = [bm.verts.new((x, y, -h / 2)) for x, y in pts]
    bm.faces.new(verts)
    bmesh.ops.contextual_create(bm, geom=bm.edges[:] + bm.verts[:])
    r_ext = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
    verts_ext = [e for e in r_ext["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, vec=(0, 0, h), verts=verts_ext)
    bm.normal_update()
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(o)
    o.location = loc
    if fillet:
        b = o.modifiers.new("fil", 'BEVEL')
        b.width = fillet; b.segments = seg; b.limit_method = 'ANGLE'
        b.angle_limit = math.radians(30)
        _mset(b, use_clamp_overlap=True, harden_normals=True, use_harden_normals=True)
    return o


def boolean(target, cutter, op='DIFFERENCE', apply=True):
    cutter.display_type = 'WIRE'
    m = target.modifiers.new("bool", 'BOOLEAN')
    m.operation = op
    m.object = cutter
    m.solver = 'EXACT'
    if apply:
        bpy.context.view_layer.objects.active = target
        try:
            bpy.ops.object.modifier_move_to_index(modifier=m.name, index=0)
        except Exception:
            pass
        bpy.ops.object.modifier_apply(modifier=m.name)
        bpy.data.objects.remove(cutter, do_unlink=True)
    return target


def box_uv_project(obj):
    """Cube-project UVs so top-mark textures land on the top face."""
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.cube_project(cube_size=1.0)
    bpy.ops.object.mode_set(mode='OBJECT')
    obj.select_set(False)


# --------------------------------------------------------------------------- lighting / world
def studio_world(strength=0.30, top=(0.55, 0.58, 0.64), bot=(0.02, 0.02, 0.025)):
    """Soft vertical-gradient environment (horizon brighter, floor dark)."""
    sc = bpy.context.scene
    w = bpy.data.worlds.new("studio"); sc.world = w
    w.use_nodes = True
    nt = w.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld");  out.location = (600, 0)
    bg = nt.nodes.new("ShaderNodeBackground");     bg.location = (400, 0)
    ramp = nt.nodes.new("ShaderNodeValToRGB");     ramp.location = (100, 0)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ");   sep.location = (-150, 0)
    mapn = nt.nodes.new("ShaderNodeMapping");      mapn.location = (-380, 0)
    tc = nt.nodes.new("ShaderNodeTexCoord");       tc.location = (-620, 0)
    nt.links.new(tc.outputs["Generated"], mapn.inputs["Vector"])
    nt.links.new(mapn.outputs["Vector"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs[0], out.inputs[0])
    mapn.inputs["Location"].default_value = (0, 0, 0.5)  # remap -0.5..0.5 -> 0..1
    # very soft sweep: dark floor -> mid ceiling, no hard band
    e = ramp.color_ramp.elements
    e[0].position = 0.05; e[0].color = (*bot, 1)
    e[1].position = 0.98
    e[1].color = (top[0] * 0.78, top[1] * 0.80, top[2] * 0.84, 1)
    mid = ramp.color_ramp.elements.new(0.62)
    mid.color = (*top, 1)
    ramp.color_ramp.interpolation = 'EASE'
    bg.inputs["Strength"].default_value = strength
    return w


def area_light(name, loc, target, energy, size, color=(1, 1, 1)):
    l = bpy.data.lights.new(name, 'AREA')
    l.energy = energy; l.size = size; l.color = color
    o = bpy.data.objects.new(name, l)
    bpy.context.collection.objects.link(o)
    o.location = loc
    d = Vector(target) - Vector(loc)
    o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return o


def three_point(center, scale):
    product_light(center, scale)


def product_light(center, scale, key=1.0):
    cx, cy, cz = center
    # large soft overhead -> the dominant, even source
    ceil = area_light("ceiling", (cx, cy - scale * 0.2, cz + scale * 3.4),
                      center, 11.0 * scale ** 2 * key, scale * 12.0)
    if hasattr(ceil.data, "spread"):
        ceil.data.spread = math.radians(170)
    # key front-right, big and soft so its reflection is a gentle wash
    area_light("key", (cx + scale * 1.7, cy - scale * 2.1, cz + scale * 1.9),
               center, 20.0 * scale ** 2 * key, scale * 3.6, color=(1.0, 0.985, 0.96))
    # broad front fill camera-left
    area_light("fill", (cx - scale * 2.6, cy - scale * 2.1, cz + scale * 1.5),
               center, 16.0 * scale ** 2, scale * 4.2, color=(0.94, 0.965, 1.0))
    # rim / kicker behind for edge separation
    area_light("rim", (cx - scale * 0.5, cy + scale * 2.3, cz + scale * 1.5),
               center, 55.0 * scale ** 2, scale * 1.2)


# --------------------------------------------------------------------------- camera / render
def make_camera(name="cam", lens=85):
    cd = bpy.data.cameras.new(name); cd.lens = lens
    cd.dof.use_dof = False
    o = bpy.data.objects.new(name, cd)
    bpy.context.collection.objects.link(o)
    bpy.context.scene.camera = o
    return o


def look_at(cam, target):
    d = Vector(target) - cam.location
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def orbit(cam, target, az_deg, el_deg, dist):
    a, e = math.radians(az_deg), math.radians(el_deg)
    cam.location = Vector(target) + Vector((
        math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e))) * dist
    look_at(cam, target)


def _has_cuda_optix():
    try:
        p = bpy.context.preferences.addons['cycles'].preferences
        for t in ('OPTIX', 'CUDA', 'HIP', 'ONEAPI'):
            try:
                p.compute_device_type = t
                p.get_devices()
                if any(d.type != 'CPU' for d in p.devices):
                    for d in p.devices:
                        d.use = (d.type != 'CPU')
                    return t
            except Exception:
                pass
    except Exception:
        pass
    return None


def render_cfg(engine='CYCLES', samples=192, res=(2000, 1250), denoise=True, transparent=False,
               exposure=-0.55, look='AgX - Medium Contrast', fast=False):
    sc = bpy.context.scene
    sc.render.engine = engine
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = transparent
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.exposure = exposure
    try:
        sc.view_settings.look = look
    except TypeError:
        sc.view_settings.look = 'None'
    if engine == 'CYCLES':
        sc.cycles.samples = samples
        sc.cycles.use_denoising = denoise
        try:
            sc.cycles.denoiser = 'OPENIMAGEDENOISE'
        except Exception:
            pass
        sc.cycles.max_bounces = 8 if fast else 14
        sc.cycles.diffuse_bounces = 3 if fast else 4
        sc.cycles.glossy_bounces = 3 if fast else 6
        sc.cycles.transmission_bounces = 2 if fast else 8
        sc.cycles.caustics_reflective = False
        sc.cycles.caustics_refractive = False
        sc.cycles.use_fast_gi = fast
        gpu = _has_cuda_optix()
        sc.cycles.device = 'GPU' if gpu else 'CPU'
        if not gpu:
            sc.render.threads_mode = 'AUTO'
        print("Cycles device:", sc.cycles.device, gpu or "(cpu)")
    else:
        sc.eevee.taa_render_samples = 16 if fast else max(48, samples // 3)
        if hasattr(sc.eevee, "use_raytracing"):
            sc.eevee.use_raytracing = not fast
        for attr, val in (("use_shadow_jitter_viewport", False),):
            if hasattr(sc.eevee, attr):
                setattr(sc.eevee, attr, val)


def ground(z=0.0, size=4000, color=(0.05, 0.05, 0.055), rough=0.5):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, z))
    o = bpy.context.active_object; o.name = "ground"
    assign(o, mat_solid("ground_mat", color, rough=rough))
    return o


def render_to(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("wrote", path)
