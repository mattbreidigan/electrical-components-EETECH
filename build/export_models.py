"""
Export delivery formats from a model .blend.
    blender <model>.blend -b -P build/export_models.py -- <basename>
Writes deliverables/models/<basename>.glb and .fbx  (quad .blend kept as-is).
"""
import bpy, os, sys

argv = sys.argv[sys.argv.index("--") + 1:]
BASE = argv[0]
OUT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "deliverables", "models"))

# select all mesh objects under the asset root
for o in bpy.data.objects:
    o.select_set(o.type in ('MESH', 'EMPTY'))

glb = os.path.join(OUT, BASE + ".glb")
bpy.ops.export_scene.gltf(filepath=glb, export_format='GLB', use_selection=True,
                          export_apply=True, export_yup=True)
print("wrote", glb)

fbx = os.path.join(OUT, BASE + ".fbx")
bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, apply_unit_scale=True,
                         apply_scale_options='FBX_SCALE_UNITS', mesh_smooth_type='FACE',
                         bake_space_transform=True)
print("wrote", fbx)
