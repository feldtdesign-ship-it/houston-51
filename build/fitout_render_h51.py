"""
fitout_render_h51.py: the render version of the build-out, made the way 178 Lafayette and 115 Avenue A were.
Opens build/houston_51.blend (the web model), saves build/houston_51_render.blend and adds to it:
  - Michael's real tees on hangers (ASSET_tee_<colourway>_0x from mott-167/build/mott_167.blend: his art on cream, navy, lilac, moss, peach) instead of the flat web tees
  - the Galaga cabinet kitty-corner in the back-east corner (as at 178)
  - the yellow ADA tactile strip, PJ yellow, along the east gallery wall the whole way down: the subway platform edge, indoors (as at 115 Avenue A)
  - black paint: back wall behind the video wall, the bath door, plinths under the tables
Headless: /Applications/Blender.app/Contents/MacOS/Blender --background --python build/fitout_render_h51.py
"""
import bpy, bmesh, math, os
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE); LOC = os.path.dirname(OUT)
SRC = os.path.join(HERE, "houston_51.blend"); DST = os.path.join(HERE, "houston_51_render.blend")
MOTT = os.path.join(LOC, "mott-167", "build", "mott_167.blend")
FT = 0.3048
X0, X1, XR, DEPTH, CEIL = 1.5, 11.5, 17.5, 67.6, 11.5
UP = [3.0 + 4.0 * k for k in range(10)]; RZ, RO = 5.0, 1.1; TEE_PITCH = 0.35; HOOK = 0.022
BAY = ('cream', 'navy', 'lilac', 'moss', 'peach', 'cream', 'navy', 'lilac', 'moss')
def root(): return bpy.data.objects["H51_IN"]
def srgb(h, a=1.0):
    h = h.lstrip('#'); r, g, b = (int(h[i:i+2], 16) / 255 for i in (0, 2, 4)); f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b), a)
def mat_flat(name, hexc, rough=0.7, metal=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True; p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    p.inputs['Base Color'].default_value = srgb(hexc); p.inputs['Roughness'].default_value = rough; p.inputs['Metallic'].default_value = metal; return m
def coll(name):
    c = bpy.data.collections.get(name)
    if not c: c = bpy.data.collections.new(name); bpy.context.scene.collection.children.link(c)
    return c
def mesh_obj(name, bm, mat, c):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); c.objects.link(o); o.data.materials.append(mat); o.parent = root(); return o
def box(name, x0, x1, y0, y1, z0, z1, mat, c):
    bm = bmesh.new(); x0, x1, y0, y1, z0, z1 = [v * FT for v in (x0, x1, y0, y1, z0, z1)]
    vs = [bm.verts.new(p) for p in ((x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1))]
    for f in ((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)): bm.faces.new([vs[i] for i in f])
    return mesh_obj(name, bm, mat, c)
def append_assets():
    names = ['Coin-op Arcade Game Cabinet Galaga'] + ['ASSET_tee_%s_%02d' % (cw, i) for cw in ('cream', 'navy', 'lilac', 'moss', 'peach', 'black', 'white') for i in (1, 2, 3)]
    with bpy.data.libraries.load(MOTT, link=False) as (src, dst): dst.collections = [n for n in names if n in src.collections]
    got = 0
    for n in names:
        c = bpy.data.collections.get(n)
        if not c: continue
        if c.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(c)
        lc = bpy.context.view_layer.layer_collection.children.get(c.name)
        if lc: lc.exclude = True
        got += 1
    return "assets: %d collections" % got
def real_tees():
    for o in [o for o in bpy.data.objects if o.name in ('FIT_STRIP', 'FIT_BLACKWALL')]: bpy.data.objects.remove(o, do_unlink=True)
    for o in [o for o in bpy.data.objects if o.name.startswith("FIT_TEE_")]: bpy.data.objects.remove(o, do_unlink=True)
    c = coll("RenderTees"); n = 0; z = RZ + 0.045 - HOOK / FT
    for k, (a, b) in enumerate(zip(UP, UP[1:])):
        cw = BAY[k % len(BAY)]; y = a + 0.5; i = 0
        while y < b - 0.45:
            ac = bpy.data.collections.get('ASSET_tee_%s_%02d' % (cw, i % 3 + 1))
            if not ac: return 'tee assets missing'
            e = bpy.data.objects.new('RTEE_%03d' % n, None); e.instance_type = 'COLLECTION'; e.instance_collection = ac; e.empty_display_size = 0.1
            e.location = ((X1 - RO) * FT, y * FT, z * FT); e.rotation_euler = (0, 0, math.radians(90)); c.objects.link(e); e.parent = root(); n += 1; i += 1; y += TEE_PITCH
    return "%d real tees on the rail" % n
def galaga():
    ac = bpy.data.collections.get('Coin-op Arcade Game Cabinet Galaga')
    if not ac: return 'galaga missing'
    pts = [o.matrix_world @ Vector(b) for o in ac.all_objects if o.type == 'MESH' for b in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))); hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    ac.instance_offset = ((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z)
    e = bpy.data.objects.new('galaga_inst', None); e.instance_type = 'COLLECTION'; e.instance_collection = ac; coll("RenderTees").objects.link(e); e.parent = root()
    e.location = ((X0 + 2.5) * FT, (DEPTH - 2.5) * FT, 0.06 * FT); e.rotation_euler = (0, 0, math.radians(45)); return "galaga kitty-corner, back-east"
def yellow_strip():
    """ADA tactile warning strip: a 1 ft yellow slab down the east wall, truncated domes on a 2.35 in grid"""
    c = coll("RenderStrip"); yel = mat_flat("ada_yellow", "#FFD000", 0.45); x0, x1, y0, y1 = X0, X0 + 1.0, 0.4, 66.4
    box("STRIP_SLAB", x0, x1, y0, y1, 0.06, 0.09, yel, c)
    bm = bmesh.new(); pitch = 0.235; r = 0.062; h = 0.03; n = 0; y = y0 + 0.12
    while y < y1 - 0.1:
        for j in range(5):
            x = x0 + 0.1 + j * 0.2 + (0.098 if int((y - y0) / pitch) % 2 else 0)
            if x > x1 - 0.06: continue
            bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=r * FT, radius2=r * 0.7 * FT, depth=h * FT)
            vs = [v for v in bm.verts][-18:]; bmesh.ops.translate(bm, vec=(x * FT, y * FT, (0.09 + h / 2) * FT), verts=vs); n += 1
        y += pitch
    mesh_obj("STRIP_DOMES", bm, yel, c); return "yellow strip %d domes" % n
def black_paint():
    c = coll("RenderBlack"); blk = mat_flat("paint_black", "#0c0c0c", 0.5)
    box("BLACK_BACKWALL", X0, XR, DEPTH - 0.03, DEPTH, 0.06, CEIL, blk, c)                              # the wall behind the video wall, painted out
    for i, (ya, yb) in enumerate(((13.0, 18.5), (23.0, 28.5))): box("BLACK_PLINTH_%d" % i, 4.7, 8.3, ya + 0.3, yb - 0.3, 0.06, 0.45, blk, c)      # black plinths under the tables, as at 115
    return "black paint: back wall, plinths"
if bpy.app.background:
    bpy.ops.wm.open_mainfile(filepath=SRC)
    print(append_assets()); print(real_tees()); print(galaga()); print(yellow_strip()); print(black_paint())
    bpy.ops.wm.save_as_mainfile(filepath=DST); print("FITOUT DONE", flush=True)
