"""Convert GLB models into files TouchDesigner reads (its FBX COMP rejects .glb).

    blender --background --factory-startup --python convert_models.py -- <list.json> <out_dir>

list.json is {"slug": "path/to/model.glb", ...}. For each model this writes
<out_dir>/<slug>/model.obj (one joined mesh, for File In POP/SOP), model.fbx
(for the FBX COMP), basecolor.png when the model has a base colour image, and
info.json. Every model is centred on the origin and scaled so its longest
side is 1 unit, Y up, so scenes can swap models without re-framing.
"""

import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

MAX_TRIS = 120_000


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def base_colour_image(obj):
    for slot in obj.material_slots:
        mat = slot.material
        if not mat or not mat.use_nodes:
            continue
        for node in mat.node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                link = node.inputs["Base Color"].links
                if link and link[0].from_node.type == "TEX_IMAGE" and link[0].from_node.image:
                    return link[0].from_node.image
    return None


def convert(slug, src, out_dir):
    reset()
    bpy.ops.import_scene.gltf(filepath=str(src))
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not meshes:
        return {"slug": slug, "error": "no meshes"}
    parts = len(meshes)
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    # Bake parent transforms into the meshes before joining.
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    if parts > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    corners = [Vector(c) for c in obj.bound_box]
    lo = Vector((min(c[i] for c in corners) for i in range(3)))
    hi = Vector((max(c[i] for c in corners) for i in range(3)))
    size = hi - lo
    longest = max(size) or 1.0
    centre = (lo + hi) / 2
    for v in obj.data.vertices:
        v.co = (v.co - centre) / longest
    obj.data.update()

    obj.data.calc_loop_triangles()
    tris = len(obj.data.loop_triangles)
    decimated = False
    if tris > MAX_TRIS:
        mod = obj.modifiers.new("dec", "DECIMATE")
        mod.ratio = MAX_TRIS / tris
        bpy.ops.object.modifier_apply(modifier=mod.name)
        obj.data.calc_loop_triangles()
        decimated = True

    dest = Path(out_dir) / slug
    dest.mkdir(parents=True, exist_ok=True)
    image = base_colour_image(obj)
    has_texture = False
    if image is not None:
        try:
            image.filepath_raw = str(dest / "basecolor.png")
            image.file_format = "PNG"
            image.save()
            has_texture = True
        except Exception as exc:  # packed images occasionally refuse to save
            print("TEXTURE FAIL", slug, exc)

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.wm.obj_export(
        filepath=str(dest / "model.obj"),
        export_selected_objects=True,
        export_materials=False,
        export_normals=True,
        export_uv=True,
        export_triangulated_mesh=True,
        forward_axis="NEGATIVE_Z",
        up_axis="Y",
    )
    fbx_ok = True
    try:
        bpy.ops.export_scene.fbx(
            filepath=str(dest / "model.fbx"),
            use_selection=True,
            path_mode="COPY",
            embed_textures=True,
            axis_forward="-Z",
            axis_up="Y",
        )
    except Exception as exc:
        fbx_ok = False
        print("FBX FAIL", slug, exc)

    info = {
        "slug": slug,
        "source": str(src),
        "parts_joined": parts,
        "vertices": len(obj.data.vertices),
        "triangles": len(obj.data.loop_triangles),
        "decimated": decimated,
        "original_size_m": [round(s, 4) for s in size],
        "size_units": [round(s / longest, 4) for s in (size.x, size.z, size.y)],
        "has_uv": bool(obj.data.uv_layers),
        "has_texture": has_texture,
        "fbx": fbx_ok,
    }
    (dest / "info.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    return info


def main():
    args = sys.argv[sys.argv.index("--") + 1 :]
    models = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    out_dir = Path(args[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    results = {}
    for slug, src in models.items():
        try:
            results[slug] = convert(slug, src, out_dir)
        except Exception as exc:
            results[slug] = {"slug": slug, "error": repr(exc)}
        print("MODEL", slug, json.dumps(results[slug]))
    (out_dir / "library.json").write_text(json.dumps(results, indent=1), encoding="utf-8")


main()
