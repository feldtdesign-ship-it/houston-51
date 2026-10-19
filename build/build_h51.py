"""
build_h51.py
51 East Houston Street (Nolita, Meridian Retail Leasing, 1,400 sf, ~68 ft deep) from the NYC Open Data layers in data/ (pulled by build/pull.py).
Same build as lafayette-178/build/build_178.py, re-pointed, with three layers inside the long room (named so the page can switch them):
  EX_*   the space AS FOUND (hex marble floor, wood patch, black hex tile wall + rosette, steel portals, slate rear floor)  -> the page peels these away
  IN_*   the WHITE BOX under them (floor, walls, ceiling, track)                                                            -> stays
  FIT_*  PJ's shop (prints east wall, pipe-and-plank tees west wall, tables)  and  MON_SCR_*  the 15 video screens the page plays clips on
Headless (never his open Blender):  /Applications/Blender.app/Contents/MacOS/Blender --background --python build/build_h51.py
Plan source: Meridian brochure (plan 67'-7" long, 39'-10" to the bath, 9'-11" at the glass, rear room wider); storefront from his video (window left, glass door right, black steel).
The upper floors are NOT photographed: drawn from the city's height (60.74 ft) and floor count (5).
Room frame (feet, parented to H51_IN): x from the EAST corner of the front, going west along the glass; y into the building; z up. Outside the glass is y < 0.
"""
import bpy, bmesh, json, math, os, glob
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else "/Users/michaelweinfeld/Documents/2026/PJ O'Rourke/Location Research/houston-51/build"
OUT_DIR = os.path.dirname(HERE); DATA_DIR = os.path.join(OUT_DIR, "data"); ART_DIR = os.path.join(HERE, "art")
SITE_LAT, SITE_LON = 40.724565, -73.994625
SITES = {"1005090023": ("SITE_51", "PJ_BRICK"), "1005090021": ("SITE_W", "PJ_TAN"), "1005090026": ("SITE_E", "PJ_CREAM")}
FT = 0.3048; H_FALLBACK = 9.0; COLLECTION = "H51"
PALETTE = {"PJ_INK": "2A2724", "PJ_GROUND": "141210", "PJ_ROAD": "1C1A18", "PJ_WALK": "2B2823", "PJ_MEDIAN": "34302A", "PJ_TREE": "4A5A3A",
           "PJ_LABEL": "8A857C", "PJ_GLASS": "0D1714", "PJ_SHOPGLASS": "A9B8B4", "PJ_IRON": "121212", "PJ_CREAM": "D9CBA8", "PJ_BRICK": "8F5A48",
           "PJ_TAN": "B89B72", "PJ_TRIM": "C9C2B4", "PJ_ALU": "B8BABD", "PJ_STONE": "B9B5AC"}
COSL = math.cos(math.radians(SITE_LAT))
def proj(lon, lat): return ((lon - SITE_LON) * 111320.0 * COSL, (lat - SITE_LAT) * 110540.0)
def srgb(h, a=1.0):
    h = h.lstrip('#'); r, g, b = (int(h[i:i+2], 16) / 255 for i in (0, 2, 4))
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b), a)
def principled(m): return next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
def mat_flat(name, hexc, rough=0.8, metal=0.0):
    m = bpy.data.materials.get(name)
    if not m: m = bpy.data.materials.new(name); m.use_nodes = True
    p = principled(m); p.inputs['Base Color'].default_value = srgb(hexc); p.inputs['Roughness'].default_value = rough; p.inputs['Metallic'].default_value = metal
    m.diffuse_color = srgb(hexc); return m
def make_materials():
    for name, hexc in PALETTE.items(): mat_flat(name, hexc, 0.95)
    m = bpy.data.materials["PJ_SHOPGLASS"]; b = principled(m); b.inputs["Alpha"].default_value = 0.10
    for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND"), ("use_backface_culling", False)):
        try: setattr(m, attr, val)
        except Exception: pass
def image_mat(name, path):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputMaterial'); p = nt.nodes.new('ShaderNodeBsdfPrincipled'); tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(path, check_existing=True); nt.links.new(tex.outputs['Color'], p.inputs['Base Color']); p.inputs['Roughness'].default_value = 0.8
    nt.links.new(p.outputs[0], out.inputs[0]); return m

def load(key):
    p = os.path.join(DATA_DIR, key + ".json")
    if not os.path.exists(p): return []
    out = []
    for r in json.load(open(p)):
        g = r.get("the_geom") or r.get("multipolygon") or r.get("geometry")
        if g: out.append({"properties": r, "geometry": g})
    return out
def rings(geom):
    t = geom.get("type"); c = geom.get("coordinates", [])
    if t == "Polygon": return [c[0]] if c else []
    if t == "MultiPolygon": return [p[0] for p in c if p]
    return []
def contours(geom):
    t = geom.get("type"); c = geom.get("coordinates", [])
    src = [c] if t == "Polygon" else (c if t == "MultiPolygon" else [])
    for poly in src:
        out = []
        for ring in poly:
            pts = [proj(a, b) for a, b in ring]; cl = []
            for p in pts:
                if not cl or abs(p[0]-cl[-1][0]) > 1e-7 or abs(p[1]-cl[-1][1]) > 1e-7: cl.append(p)
            if len(cl) > 2 and abs(cl[0][0]-cl[-1][0]) < 1e-7 and abs(cl[0][1]-cl[-1][1]) < 1e-7: cl = cl[:-1]
            if len(cl) >= 3: out.append(cl)
        if out: yield out
def get_collection():
    old = bpy.data.collections.get(COLLECTION)
    if old:
        for o in list(old.objects): bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.collections.remove(old)
    c = bpy.data.collections.new(COLLECTION); bpy.context.scene.collection.children.link(c); return c
def col(): return bpy.data.collections.get(COLLECTION) or get_collection()
def extrude_ring(bm, xy, z0, z1):
    cl = []
    for p in xy:
        if not cl or abs(p[0]-cl[-1][0]) > 1e-6 or abs(p[1]-cl[-1][1]) > 1e-6: cl.append(p)
    if len(cl) > 2 and abs(cl[0][0]-cl[-1][0]) < 1e-6 and abs(cl[0][1]-cl[-1][1]) < 1e-6: cl = cl[:-1]
    if len(cl) < 3: return False
    vs = [bm.verts.new((p[0], p[1], z0)) for p in cl]
    try: face = bm.faces.new(vs)
    except ValueError: return False
    res = bmesh.ops.extrude_face_region(bm, geom=[face])
    bmesh.ops.translate(bm, vec=(0, 0, z1 - z0), verts=[v for v in res["geom"] if isinstance(v, bmesh.types.BMVert)])
    return True
def mesh_from_bm(bm, name, mat):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); col().objects.link(ob); ob.data.materials.append(bpy.data.materials[mat]); return ob

def stage_massing():
    make_materials(); get_collection(); feats = load("footprints")
    bases = [float(f["properties"].get("ground_elevation") or 0) for f in feats if f["properties"].get("base_bbl") in SITES]
    base = sum(bases) / len(bases) if bases else 0.0
    bm = bmesh.new(); n = 0; guessed = 0
    for f in feats:
        p = f["properties"]
        if p.get("base_bbl") in SITES: continue
        try: h_ft = float(p.get("height_roof") or 0)
        except ValueError: h_ft = 0.0
        h = h_ft * FT
        if h <= 0: h = H_FALLBACK; guessed += 1
        ge = (float(p.get("ground_elevation") or base) - base) * FT
        for ring in rings(f["geometry"]):
            if extrude_ring(bm, [proj(a, b) for a, b in ring], ge, ge + h): n += 1
    mesh_from_bm(bm, "NOLITA_MASSING", "PJ_INK")
    return "massing: {} solids, {} without height".format(n, guessed)
def build_flat(key, name, z, mat):
    verts, faces = [], []
    for f in load(key):
        for cont in contours(f["geometry"]):
            vecs = [[Vector((x, y, 0.0)) for (x, y) in ring] for ring in cont]; flat = [v for ring in vecs for v in ring]; b = len(verts)
            try: idx = tessellate_polygon(vecs)
            except Exception: continue
            verts.extend([(v.x, v.y, z) for v in flat]); faces.extend([(b+t[0], b+t[1], b+t[2]) for t in idx])
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    ob = bpy.data.objects.new(name, me); col().objects.link(ob); ob.data.materials.append(bpy.data.materials[mat]); return "{}: {} tris".format(name, len(faces))
def stage_flat(): return "; ".join([build_flat("roadbed", "ROADBED", 0.02, "PJ_ROAD"), build_flat("sidewalk", "SIDEWALK", 0.14, "PJ_WALK"), build_flat("median", "MEDIAN", 0.18, "PJ_MEDIAN")])
def at_fraction(pts, frac):
    segs = [math.dist(pts[i], pts[i+1]) for i in range(len(pts)-1)]; total = sum(segs); want = total * frac; run = 0.0
    for i, s in enumerate(segs):
        if run + s >= want:
            t = (want - run) / s if s else 0.0; a, b = pts[i], pts[i+1]
            return ((a[0] + (b[0]-a[0])*t, a[1] + (b[1]-a[1])*t), math.atan2(b[1]-a[1], b[0]-a[0]))
        run += s
    return pts[-1], math.atan2(pts[-1][1]-pts[0][1], pts[-1][0]-pts[0][0])
def stage_labels(size=12.0, min_gap=34.0):
    longest = {}
    for f in load("centerline"):
        n = (f["properties"].get("stname_label") or "").strip()
        if not n: continue
        g = f["geometry"]; parts = g["coordinates"] if g["type"] == "MultiLineString" else [g["coordinates"]]
        for line in parts:
            pts = [proj(a, b) for a, b in line]; L = sum(math.dist(pts[i], pts[i+1]) for i in range(len(pts)-1))
            if n not in longest or L > longest[n][0]: longest[n] = (L, pts)
    placed = []
    for name, (L, pts) in sorted(longest.items(), key=lambda kv: -kv[1][0]):
        if L < 40: continue
        spot = None
        for frac in (0.5, 0.3, 0.7, 0.18, 0.82):
            p, ang = at_fraction(pts, frac)
            if all(math.dist(p, q) > min_gap for q in placed): spot = (p, ang); break
        if spot is None: spot = at_fraction(pts, 0.5)
        p, ang = spot
        if ang > math.pi/2: ang -= math.pi
        if ang < -math.pi/2: ang += math.pi
        cu = bpy.data.curves.new("ST_" + name, type='FONT'); cu.body = name; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'; cu.size = size; cu.extrude = 0.04; cu.space_character = 1.15
        ob = bpy.data.objects.new("ST_" + name, cu); col().objects.link(ob); ob.location = (p[0], p[1], 0.6); ob.rotation_euler = (0, 0, ang); ob.data.materials.append(bpy.data.materials["PJ_LABEL"]); placed.append(p)
    return "labels: {}".format(len(placed))
def stage_trees():
    rows = [r for r in json.load(open(os.path.join(DATA_DIR, "trees.json"))) if r.get("status") == "Alive"]
    bm = bmesh.new(); n = 0
    for t in rows:
        try: x, y = proj(float(t["longitude"]), float(t["latitude"])); dbh = float(t.get("tree_dbh") or 6)
        except (TypeError, ValueError, KeyError): continue
        r = max(1.4, min(4.2, 1.2 + dbh * 0.12)); h = max(4.0, min(11.0, 3.5 + dbh * 0.35))
        tb = bmesh.new(); bmesh.ops.create_icosphere(tb, subdivisions=1, radius=1.0); bmesh.ops.scale(tb, vec=(r, r, r * 0.8), verts=tb.verts); bmesh.ops.translate(tb, vec=(x, y, h), verts=tb.verts)
        me = bpy.data.meshes.new("t"); tb.to_mesh(me); tb.free(); bm.from_mesh(me); bpy.data.meshes.remove(me); n += 1
    mesh_from_bm(bm, "TREES", "PJ_TREE"); return "trees: {}".format(n)
def stage_ground():
    bpy.ops.mesh.primitive_plane_add(size=2000, location=(0, 0, -0.3)); g = bpy.context.active_object; g.name = "GROUND"
    for c in g.users_collection: c.objects.unlink(g)
    col().objects.link(g); return "ground"

# ---------- the three fronts on East Houston ----------
# Frame per face: a = EAST corner of the front, b = WEST corner. x = feet from a going west; d = metres out over the sidewalk (north-north-east); z up.
GF = 12.0 * FT
ROOF = {"51": 60.74 * FT, "W": 62.34 * FT, "E": 60.34 * FT}
E_VEC = (math.sin(math.radians(119)), math.cos(math.radians(119)))   # street direction, east-ish
N_VEC = (math.sin(math.radians(29)), math.cos(math.radians(29)))     # outward from the Houston fronts
def _box(bm, x0, x1, y0, y1, z0, z1):
    x0, x1 = min(x0, x1), max(x0, x1); y0, y1 = min(y0, y1), max(y0, y1); z0, z1 = min(z0, z1), max(z0, z1)
    vs = [bm.verts.new(p) for p in ((x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1))]
    for f in ((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)): bm.faces.new([vs[i] for i in f])
def _front(bbl):
    """(east corner, west corner) in lon/lat of the Houston edge of a lot: the edge whose midpoint lies furthest toward the street (north-north-east)."""
    for f in load("footprints"):
        if f["properties"].get("base_bbl") != bbl: continue
        ring = rings(f["geometry"])[0]; pts = [(proj(a, b), (a, b)) for a, b in ring]; best = None
        for i in range(len(pts) - 1):
            (p, pl), (q, ql) = pts[i], pts[i + 1]
            if math.dist(p, q) < 6.0: continue
            mid = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2); score = mid[0] * N_VEC[0] + mid[1] * N_VEC[1]
            if best is None or score > best[0]: best = (score, pl, ql, p, q)
        _, pl, ql, p, q = best
        return (pl, ql) if (p[0] * E_VEC[0] + p[1] * E_VEC[1]) > (q[0] * E_VEC[0] + q[1] * E_VEC[1]) else (ql, pl)
    raise RuntimeError("no footprint " + bbl)
def _face(name, a_ll, b_ll, draw, side=-1, prefix="B51_"):
    a = proj(*a_ll); b = proj(*b_ll); ang = math.atan2(b[1]-a[1], b[0]-a[0]); L = math.dist(a, b) / FT
    parts = {}
    def B(mat, x0, x1, d0, d1, z0, z1): _box(parts.setdefault(mat, bmesh.new()), x0 * FT, x1 * FT, side * d0, side * d1, z0, z1)
    cuts = []
    def CUT(x0, x1, d0, d1, z0, z1): cuts.append((x0 * FT, x1 * FT, side * d0, side * d1, z0, z1))
    B.cut = CUT
    draw(B, L)
    root = bpy.data.objects.new(prefix + name, None); col().objects.link(root); root.location = (a[0], a[1], 0.14); root.rotation_euler = (0, 0, ang)
    for mat, bm in parts.items():
        if not bm.faces: bm.free(); continue
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces); me = bpy.data.meshes.new(prefix + name + "_" + mat[3:]); bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new(prefix + name + "_" + mat[3:], me); col().objects.link(ob); ob.parent = root; ob.data.materials.append(bpy.data.materials[mat])
    for i, c in enumerate(cuts):
        cb = bmesh.new(); _box(cb, *c); me = bpy.data.meshes.new("CUT"); cb.to_mesh(me); cb.free()
        co = bpy.data.objects.new(prefix + "CUT_%s_%d" % (name, i), me); col().objects.link(co); co.parent = root; co.hide_render = True; co.display_type = 'WIRE'
    return root, L
def _win(B, x0, x1, z0, z1, panes=1, d=0.0, glass="PJ_GLASS", frame="PJ_IRON", f=0.25):
    B(glass, x0, x1, d + 0.00, d + 0.04, z0, z1)
    for xx in [x0 + (x1 - x0) * i / panes for i in range(panes + 1)]: B(frame, xx - f / 2, xx + f / 2, d - 0.01, d + 0.07, z0, z1)
    for zz in (z0, z1): B(frame, x0 - f / 2, x1 + f / 2, d - 0.01, d + 0.07, zz - 0.04, zz + 0.04)
def _uppers(B, L, gf, roof, nfl, bays, w=3.3, h=5.4, sill=2.7, cornice="PJ_TRIM"):
    fh = (roof - gf) / (nfl - 1)
    for fl in range(nfl - 1):
        z = gf + fl * fh
        for cx in bays:
            _win(B, cx - w / 2, cx + w / 2, z + sill * FT, z + (sill + h) * FT, panes=2, d=-0.12, glass="PJ_GLASS")
            B("PJ_TRIM", cx - w / 2 - 0.3, cx + w / 2 + 0.3, -0.12, 0.06, z + sill * FT - 0.08, z + sill * FT)
    B(cornice, -0.1, L + 0.1, -0.02, 0.22, roof - 0.35, roof + 0.05)            # cornice and coping
# the lease, from the Meridian plan (feet, room frame): corridor 10 ft wide to the bath, wider rear room; ceiling 11.5 ft
X0, X1 = 1.5, 11.5; XR = 17.5; Y_BATH0, Y_BATH1 = 40.0, 47.0; DEPTH = 67.6; CEIL = 11.5; T = 0.5
WIN = (1.7, 6.9); DOOR = (6.9, 11.3)
def _h51(B, L):
    B.cut(X0, X1, -(Y_BATH0 + 0.6) * FT, 0.05, 0.0, CEIL * FT)                         # corridor, open at the front
    B.cut(X0, XR, -(DEPTH + 0.6) * FT, -(Y_BATH0 - 0.4) * FT, 0.0, CEIL * FT)           # bath zone and rear room
    B.cut(12.5, 16.9, -(39.0) * FT, 0.05, 0.0, 9.0 * FT)                                # the apartment hall beside it
    FR = 0.3
    B("PJ_IRON", WIN[0], WIN[1], -0.02, 0.10, 0.0, 1.3 * FT)                             # stall riser
    _win(B, WIN[0], WIN[1], 1.3 * FT, 9.0 * FT, panes=1, d=0.02, glass="PJ_SHOPGLASS", f=FR)
    B("PJ_IRON", DOOR[0], DOOR[1], 0.02, 0.09, 0.0, 0.08)
    for xx in (DOOR[0], DOOR[1] - FR): B("PJ_IRON", xx, xx + FR, -0.01, 0.10, 0.0, 9.0 * FT)
    B("PJ_IRON", DOOR[0], DOOR[1], -0.01, 0.10, 7.6 * FT, 7.6 * FT + 0.1)                 # transom bar
    B("PJ_SHOPGLASS", DOOR[0] + FR, DOOR[1] - FR, 0.03, 0.06, 0.15, 7.5 * FT)             # the glass door (leaf)
    B("PJ_IRON", DOOR[0] + FR, DOOR[0] + FR + 0.15, 0.02, 0.08, 0.1, 7.5 * FT); B("PJ_IRON", DOOR[1] - FR - 0.15, DOOR[1] - FR, 0.02, 0.08, 0.1, 7.5 * FT)
    B("PJ_IRON", DOOR[0] + 0.8, DOOR[1] - 0.8, 0.09, 0.14, 3.85 * FT, 4.0 * FT)           # pull bar
    B("PJ_SHOPGLASS", DOOR[0] + FR, DOOR[1] - FR, 0.03, 0.06, 7.7 * FT, 8.9 * FT)         # transom glass
    B("PJ_IRON", X0 - 0.4, X1 + 0.4, 0.0, 0.28, 9.0 * FT, GF)                             # black fascia, sign band
    B("PJ_BRICK", 0, X0 - 0.4, -0.02, 0.10, 0.0, GF); B("PJ_BRICK", X1 + 0.4, 13.1, -0.02, 0.10, 0.0, GF)
    # apartment door and the bar bay beside it
    B("PJ_IRON", 13.4, 16.6, 0.02, 0.08, 0.12, 7.4 * FT); _win(B, 13.4, 16.6, 7.5 * FT, 9.0 * FT, panes=1, d=0.02)
    B("PJ_STONE", 13.0, 17.0, 0.0, 0.35, 0.0, 0.12); B("PJ_BRICK", 13.1, 18.0, -0.02, 0.10, 9.0 * FT, GF)
    B("PJ_BRICK", 16.8, 18.0, -0.02, 0.10, 0.0, 9.0 * FT)
    _win(B, 18.2, 24.0, 1.6 * FT, 9.0 * FT, panes=2, d=0.02, glass="PJ_GLASS", f=0.3)
    B("PJ_IRON", 18.0, L, 0.0, 0.24, 9.0 * FT, GF); B("PJ_IRON", 18.0, 24.3, -0.02, 0.10, 0.0, 1.6 * FT)
    if L > 24.3: B("PJ_BRICK", 24.3, L, -0.02, 0.10, 0.0, 9.0 * FT)
    _uppers(B, L, GF, ROOF["51"], 5, (L * 0.17, L * 0.5, L * 0.83))
def _generic(roofkey, wall_light):
    def f(B, L):
        B("PJ_IRON", -0.1, L + 0.1, -0.02, 0.22, 9.2 * FT, GF)
        B("PJ_IRON", 0, L, -0.02, 0.08, 0.0, 1.2 * FT)
        _win(B, 1.0, L * 0.62, 1.2 * FT, 9.2 * FT, panes=2, d=0.02, glass="PJ_SHOPGLASS", frame="PJ_IRON")
        _win(B, L * 0.7, L - 1.0, 0.12, 9.2 * FT, panes=1, d=0.02, glass="PJ_SHOPGLASS", frame="PJ_IRON")
        _uppers(B, L, GF, ROOF[roofkey], 5, (L * 0.2, L * 0.5, L * 0.8))
    return f
def stage_sites():
    for f in load("footprints"):
        p = f["properties"]
        if p.get("base_bbl") not in SITES: continue
        name, mat = SITES[p["base_bbl"]]; h = float(p.get("height_roof") or 60) * FT; bm = bmesh.new()
        for ring in rings(f["geometry"]): extrude_ring(bm, [proj(a, b) for a, b in ring], 0.0, h)
        mesh_from_bm(bm, name, mat)
    return "sites: " + ", ".join(v[0] for v in SITES.values())
def _apply_cuts(site_name, prefix):
    bpy.context.view_layer.update(); site = bpy.data.objects.get(site_name)
    for co in [o for o in bpy.data.objects if o.name.startswith(prefix + "CUT_")]:
        m = site.modifiers.new("cut", 'BOOLEAN'); m.operation = 'DIFFERENCE'; m.object = co
        try: m.solver = 'EXACT'
        except Exception: pass
        with bpy.context.temp_override(object=site, active_object=site): bpy.ops.object.modifier_apply(modifier=m.name)
        bpy.data.objects.remove(co, do_unlink=True)
def stage_building():
    r51, L = _face("HOUSTON", *_front("1005090023"), _h51)
    _face("HOUSTON", *_front("1005090021"), _generic("W", "tan"), prefix="BW_")
    _face("HOUSTON", *_front("1005090026"), _generic("E", "cream"), prefix="BE_")
    _apply_cuts("SITE_51", "B51_")
    return "building: 51 front {:.1f} ft".format(L)

# ---------- the room: shell (IN_), as found (EX_), fit-out (FIT_ / MON_) ----------
def root(): return bpy.data.objects["H51_IN"]
def mesh_obj(name, bm, mat, recalc=True):
    if recalc: bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); col().objects.link(o); o.data.materials.append(mat); o.parent = root(); return o
def box(name, x0, x1, y0, y1, z0, z1, mat):
    bm = bmesh.new(); _box(bm, x0 * FT, x1 * FT, y0 * FT, y1 * FT, z0 * FT, z1 * FT); return mesh_obj(name, bm, mat)
def pipe(name, p0, p1, mat, r=0.07, seg=10):
    bm = bmesh.new(); a = Vector(p0) * FT; b = Vector(p1) * FT; d = b - a
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r * FT, radius2=r * FT, depth=d.length)
    bmesh.ops.transform(bm, matrix=d.to_track_quat('Z', 'Y').to_matrix().to_4x4(), verts=bm.verts); bmesh.ops.translate(bm, vec=(a + b) / 2, verts=bm.verts)
    return mesh_obj(name, bm, mat)
def quad(name, x0, x1, z0, z1, y, facing, mat):
    """a flat screen or print at y, facing -y (toward the street, facing=-1) or +y (facing=+1); u runs left to right as the viewer sees it, so video is never mirrored"""
    bm = bmesh.new()
    if facing < 0: pts = [((x0, y, z0), (0, 0)), ((x1, y, z0), (1, 0)), ((x1, y, z1), (1, 1)), ((x0, y, z1), (0, 1))]
    else:          pts = [((x1, y, z0), (0, 0)), ((x0, y, z0), (1, 0)), ((x0, y, z1), (1, 1)), ((x1, y, z1), (0, 1))]
    vs = [bm.verts.new((p[0] * FT, p[1] * FT, p[2] * FT)) for p, _ in pts]; f = bm.faces.new(vs); uv = bm.loops.layers.uv.new()
    for loop, (_, t) in zip(f.loops, pts): loop[uv].uv = t
    return mesh_obj(name, bm, mat, recalc=False)
def quad_x(name, y0, y1, z0, z1, x, mat):
    """a print on the east wall facing +x; u runs with y"""
    bm = bmesh.new(); pts = [((x, y0, z0), (0, 0)), ((x, y1, z0), (1, 0)), ((x, y1, z1), (1, 1)), ((x, y0, z1), (0, 1))]
    vs = [bm.verts.new((p[0] * FT, p[1] * FT, p[2] * FT)) for p, _ in pts]; f = bm.faces.new(vs); uv = bm.loops.layers.uv.new()
    for loop, (_, t) in zip(f.loops, pts): loop[uv].uv = t
    return mesh_obj(name, bm, mat, recalc=False)
def hexgrid(name, mat, x0, x1, y0, y1, z, R, gap, thick=0.03, skip=None):
    """a field of hexagonal tiles (pointy toward +y), centres inside the rectangle"""
    bm = bmesh.new(); w = math.sqrt(3) * R; n = 0; r = R - gap
    j = 0; y = y0 + R
    while y <= y1 - R + 1e-6:
        x = x0 + w / 2 + (w / 2 if j % 2 else 0); i = 0
        while x <= x1 - w / 2 + 1e-6:
            if not (skip and skip(i, j)):
                vs = [bm.verts.new(((x + r * math.cos(math.radians(90 + 60 * k))) * FT, (y + r * math.sin(math.radians(90 + 60 * k))) * FT, z * FT)) for k in range(6)]
                f = bm.faces.new(vs); res = bmesh.ops.extrude_face_region(bm, geom=[f]); bmesh.ops.translate(bm, vec=(0, 0, thick * FT), verts=[v for v in res["geom"] if isinstance(v, bmesh.types.BMVert)]); n += 1
            x += w; i += 1
        y += 1.5 * R; j += 1
    return mesh_obj(name, bm, mat), n
def hexwall(name, mat, xw, y0, y1, z0, z1, R, gap, face, skip=None):
    """hexagonal tiles standing on a long wall at x = xw, facing +x (face=+1, east wall) or -x (face=-1, west wall)"""
    bm = bmesh.new(); w = math.sqrt(3) * R; r = R - gap; n = 0; j = 0; z = z0 + R
    while z <= z1 - R + 1e-6:
        y = y0 + w / 2 + (w / 2 if j % 2 else 0); i = 0
        while y <= y1 - w / 2 + 1e-6:
            if not (skip and skip(i, j)):
                vs = [bm.verts.new((xw * FT, (y + r * math.cos(math.radians(90 + 60 * k))) * FT, (z + r * math.sin(math.radians(90 + 60 * k))) * FT)) for k in range(6)]
                f = bm.faces.new(vs if face > 0 else vs[::-1]); res = bmesh.ops.extrude_face_region(bm, geom=[f])
                bmesh.ops.translate(bm, vec=(face * 0.03 * FT, 0, 0), verts=[v for v in res["geom"] if isinstance(v, bmesh.types.BMVert)]); n += 1
            y += w; i += 1
        z += 1.5 * R; j += 1
    return mesh_obj(name, bm, mat), n

def stage_room():
    for o in [o for o in bpy.data.objects if o.name.startswith("H51_IN") or o.name.startswith(("IN_", "EX_", "FIT_", "MON_"))]: bpy.data.objects.remove(o, do_unlink=True)
    _face("IN", *_front("1005090023"), lambda B, L: None, prefix="H51_")
    white = mat_flat("in_white", "#F1EFEA", 0.95); floor = mat_flat("in_floor", "#DAD7D0", 0.9); black = mat_flat("in_black", "#0f0f0f", 0.5, 0.4)
    # ---- the white box ----
    box("IN_FLOOR_A", X0, X1 + T, 0, Y_BATH0, 0.0, 0.06, floor); box("IN_FLOOR_B", X0, XR, Y_BATH0, DEPTH, 0.0, 0.06, floor); box("IN_FLOOR_HALL", 12.0, 17.0, 0, 39.5, 0.0, 0.06, floor)
    box("IN_CEIL_A", X0, X1 + T, 0, Y_BATH0, CEIL, CEIL + 0.3, white); box("IN_CEIL_B", X0, XR, Y_BATH0, DEPTH, CEIL, CEIL + 0.3, white)
    box("IN_WALLE", X0 - T, X0, 0, DEPTH + T, 0, CEIL + 0.3, white)                                          # east wall, the whole length
    box("IN_WALLW1", X1, X1 + T, 0, 42.0, 0, CEIL + 0.3, white); box("IN_WALLW1b", X1, X1 + T, 45.0, Y_BATH1, 0, CEIL + 0.3, white)
    box("IN_WALLW1c", X1, X1 + T, 42.0, 45.0, 7.2, CEIL + 0.3, white)                                         # head over the bath door
    box("IN_WALLW2", XR, XR + T, Y_BATH0 - 0.5, DEPTH + T, 0, CEIL + 0.3, white)                              # rear room, west wall
    box("IN_WALLB", X0 - T, XR + T, DEPTH, DEPTH + T, 0, CEIL + 0.3, white)                                   # back wall
    box("IN_BATHBACK", X1, XR, Y_BATH1, Y_BATH1 + T, 0, CEIL + 0.3, white); box("IN_HALLEND", 12.0, XR, 39.5, Y_BATH0 - 0.4, 0, CEIL + 0.3, white)
    box("IN_HALLWALL", 17.0, 17.5, 0, 39.5, 0, CEIL + 0.3, white)
    box("IN_BATHDOOR", X1 - 0.02, X1 + 0.12, 42.4, 44.6, 0.06, 7.1, black)
    # track lighting, the one thing the room already has: two black runs and heads every five feet
    for xx in (3.4, 9.6):
        box("IN_TRACK_%d" % xx, xx - 0.05, xx + 0.05, 0.5, Y_BATH0 - 0.5, CEIL - 0.12, CEIL - 0.02, black)
        for k in range(8): box("IN_HEAD_%d_%d" % (xx, k), xx - 0.14, xx + 0.14, 2.0 + k * 5.0 - 0.14, 2.0 + k * 5.0 + 0.14, CEIL - 0.45, CEIL - 0.12, black)
    # ---- as found ----
    marble = mat_flat("ex_marble", "#E9E8E4", 0.35); wood = mat_flat("ex_wood", "#8C7455", 0.6); slate = mat_flat("ex_slate", "#454A4F", 0.7); steel = mat_flat("ex_steel", "#0c0c0c", 0.4, 0.6)
    timber = mat_flat("ex_timber", "#D8B77A", 0.7); tile = mat_flat("ex_tilebase", "#101010", 0.4); hexw = mat_flat("ex_hexwhite", "#F4F3EF", 0.3); plaster = mat_flat("ex_plaster", "#F6F5F1", 0.9)
    grout = mat_flat("ex_grout", "#6E6B65", 0.9); box("EX_GROUT", X0, X1, 0.0, 24.0, 0.06, 0.075, grout)
    _, n1 = hexgrid("EX_HEXFLOOR", marble, X0, X1, 0.0, 24.0, 0.075, 0.72, 0.045, 0.04)
    box("EX_WOOD", X0, X1, 24.0, 30.0, 0.06, 0.10, wood)
    box("EX_SLATE", X0, XR, Y_BATH1, DEPTH, 0.06, 0.10, slate); box("EX_SLATE_C", X0, X1, 30.0, Y_BATH1, 0.06, 0.10, slate)
    for nm, xw, face in (("E", X0, 1), ("W", X1, -1)):
        box("EX_TILEWALL_" + nm, xw - (0.04 if face > 0 else -0.0), xw + (0.0 if face > 0 else 0.04), 29.0, 40.0, 0.06, 9.5, tile)
        hexwall("EX_TILEHEX_" + nm, hexw, xw + face * 0.045, 29.0, 40.0, 0.06, 9.5, 0.5, 0.03, face, skip=lambda i, j: (i * 2 + j) % 5 == 0)
    # the plaster rosette on the east wall: a disc and two rings
    for k, (rr, dd) in enumerate(((2.3, 0.10), (1.8, 0.16), (1.2, 0.22), (0.5, 0.28))):
        bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=36, radius1=rr * FT, radius2=rr * FT * 0.97, depth=dd * FT)
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=__import__('mathutils').Matrix.Rotation(math.radians(90), 3, 'Y'), verts=bm.verts)
        bmesh.ops.translate(bm, vec=((X0 + dd / 2) * FT, 26.4 * FT, 6.6 * FT), verts=bm.verts); mesh_obj("EX_ROSETTE_%d" % k, bm, plaster)
    for k, y in enumerate((1.0, 7.6, 14.2, 20.8)):                                                          # steel portals on the west wall, header beam, timber studs above
        box("EX_STEEL_COL_%d" % k, X1 - 0.75, X1, y, y + 0.55, 0.06, CEIL, steel)
    box("EX_STEEL_BEAM", X1 - 0.75, X1, 1.0, 21.35, 9.0, 9.9, steel)
    for k, y in enumerate((1.55, 7.6, 14.2)):
        for s in (0.0, 2.0, 4.0): box("EX_TIMBER_%d_%d" % (k, s), X1 - 0.45, X1 - 0.30, y + 0.6 + s, y + 0.75 + s, 9.9, CEIL - 0.1, timber)
        box("EX_TIMBER_T%d" % k, X1 - 0.45, X1 - 0.30, y + 0.6, y + 6.0, CEIL - 0.25, CEIL - 0.1, timber); box("EX_TIMBER_B%d" % k, X1 - 0.45, X1 - 0.30, y + 0.6, y + 6.0, 9.9, 10.05, timber)
    box("EX_RAD", XR - 0.7, XR - 0.05, 60.0, 62.2, 0.10, 2.4, steel)
    # ---- the fit-out ----
    oak = mat_flat("fit_oak", "#9A7549", 0.7); pipe_m = mat_flat("fit_pipe", "#1A1A1A", 0.45, 0.6); frm = mat_flat("fit_frame", "#111111", 0.5); matb = mat_flat("fit_mat", "#E6E1D3", 1.0)
    arts = sorted(glob.glob(os.path.join(ART_DIR, "art_*.jpg"))); FW, FH, FD, LIP = 16 / 12, 20 / 12, 0.07, 0.07
    ys = [4.0 + i * 4.0 for i in range(9)]
    for i, yc in enumerate(ys):                                                                             # nine prints on the east wall, one level row
        zc = 5.4; x = X0
        for nm, (ya, yb, za, zb) in (("t", (yc - FW/2, yc + FW/2, zc + FH/2 - LIP, zc + FH/2)), ("b", (yc - FW/2, yc + FW/2, zc - FH/2, zc - FH/2 + LIP)), ("l", (yc - FW/2, yc - FW/2 + LIP, zc - FH/2, zc + FH/2)), ("r", (yc + FW/2 - LIP, yc + FW/2, zc - FH/2, zc + FH/2))):
            box("FIT_GAL_FR_%s%d" % (nm, i), x, x + FD, ya, yb, za, zb, frm)
        box("FIT_GAL_MAT%d" % i, x, x + FD - 0.02, yc - FW/2 + LIP, yc + FW/2 - LIP, zc - FH/2 + LIP, zc + FH/2 - LIP, matb)
        quad_x("FIT_GAL_PRINT%d" % i, yc - 11/24, yc + 11/24, zc - 14/24, zc + 14/24, x + FD - 0.012, image_mat("print_%d" % i, arts[i % len(arts)]))
    UP = [3.0 + 4.0 * k for k in range(10)]; PZ = (6.4, 8.0); RZ = 5.0; RO = 1.1; xw = X1                      # the pipe-and-plank unit on the west wall
    for y in UP:
        pipe("FIT_UNIT_UP_%d" % y, (xw - 0.08, y, 0.06), (xw - 0.08, y, CEIL - 0.9), pipe_m); pipe("FIT_UNIT_ARM_%d" % y, (xw - 0.08, y, RZ), (xw - RO, y, RZ), pipe_m)
        for z in PZ: pipe("FIT_UNIT_BRK_%d_%d" % (y, z * 10), (xw - 0.08, y, z - 0.25), (xw - 1.0, y, z - 0.25), pipe_m)
    for a, b in zip(UP, UP[1:]):
        for z in PZ: box("FIT_UNIT_PLANK_%d_%d" % (a, z * 10), xw - 1.0, xw - 0.02, a - 0.3, b + 0.3, z - 0.12, z, oak)
        pipe("FIT_UNIT_RAIL_%d" % a, (xw - RO, a, RZ), (xw - RO, b, RZ), pipe_m, r=0.045)
    cws = [("cream", "#F2DFC0"), ("navy", "#304766"), ("lilac", "#EDD0EF"), ("moss", "#4C605E"), ("peach", "#FEA580"), ("black", "#151515"), ("white", "#F4F2EC")]
    cwm = [mat_flat("fit_cw_" + n, h, 0.95) for n, h in cws]; nt = 0
    pts = [(-0.30, 0.0), (0.30, 0.0), (0.95, -0.28), (0.95, -0.72), (0.66, -0.78), (0.62, -1.65), (-0.62, -1.65), (-0.66, -0.78), (-0.95, -0.72), (-0.95, -0.28)]
    for k, (a, b) in enumerate(zip(UP, UP[1:])):                                                           # tees on hangers, one colourway to a bay
        yy = a + 0.55
        while yy < b - 0.45:
            bm = bmesh.new(); vs = [bm.verts.new(((xw - RO + u) * FT, yy * FT, (RZ + 0.05 + v) * FT)) for u, v in pts]; f = bm.faces.new(vs); res = bmesh.ops.extrude_face_region(bm, geom=[f])
            bmesh.ops.translate(bm, vec=(0, 0.05 * FT, 0), verts=[v for v in res["geom"] if isinstance(v, bmesh.types.BMVert)]); mesh_obj("FIT_TEE_%03d" % nt, bm, cwm[k % len(cwm)]); nt += 1; yy += 0.42
    q = 0
    for a, b in zip(UP, UP[1:]):                                                                            # folded stacks on the planks
        for z in PZ:
            q += 1
            if q % 4 == 0: continue
            for t in range(4 + q % 3): box("FIT_FOLD_%d_%d" % (q, t), xw - 0.92, xw - 0.12, a + 0.4, b - 0.4, z + t * 0.085, z + (t + 1) * 0.085 - 0.012, cwm[q % len(cwm)])
    for i, (ya, yb) in enumerate(((13.0, 18.5), (23.0, 28.5))):                                             # two oak tables with stacks
        box("FIT_TBL_TOP_%d" % i, 4.6, 8.4, ya, yb, 2.45, 2.6, oak)
        for x, y in ((4.8, ya + 0.3), (8.2, ya + 0.3), (4.8, yb - 0.3), (8.2, yb - 0.3)): pipe("FIT_TBL_LEG_%d_%d_%d" % (i, x * 10, y * 10), (x, y, 0.06), (x, y, 2.45), pipe_m)
        for s in range(4):
            for t in range(5): box("FIT_FOLD_T%d_%d_%d" % (i, s, t), 4.9 + (s % 2) * 1.7, 6.2 + (s % 2) * 1.7, ya + 0.4 + (s // 2) * 2.5, ya + 2.6 + (s // 2) * 2.5, 2.6 + t * 0.085, 2.6 + (t + 1) * 0.085 - 0.012, cwm[(i * 3 + s) % len(cwm)])
    # ---- the screens: 15, every one a plane named MON_SCR_* with its own UVs; the page plays a clip on each ----
    scr = mat_flat("mon_off", "#050505", 0.3); nsc = 0
    def monitor_front(name, xc, y, zc, w, h):                                                             # frame behind, screen in front, facing the street
        box("FIT_MON_FR_" + name, xc - w/2 - 0.06, xc + w/2 + 0.06, y, y + 0.14, zc - h/2 - 0.06, zc + h/2 + 0.06, frm)
        quad("MON_SCR_" + name, xc - w/2, xc + w/2, zc - h/2, zc + h/2, y - 0.01, -1, scr)
    pw, ph = 1.75, 3.1                                                                                       # the window: three portrait 43 inch panels facing the street
    for i in range(3): monitor_front("W%d" % (i + 1), WIN[0] + 0.45 + pw / 2 + i * (pw + 0.04), 0.9, 4.6, pw, ph)
    lw, lh = 3.1, 1.75                                                                                       # the back wall: a 3 by 2 video wall of 43 inch landscape panels
    for r in range(2):
        for c in range(3): monitor_front("B%d" % (r * 3 + c + 1), 9.5 + (c - 1) * (lw + 0.05), DEPTH - 0.16, 4.2 + (1 - r) * (lh + 0.05), lw, lh)
    for i, y in enumerate((9.0, 20.5, 33.0)):                                                                # three double-sided panels hung from the ceiling down the corridor
        xc = 6.5; zc = 8.0; pipe("FIT_HANG_POLE_%d" % i, (xc, y, zc + lh / 2), (xc, y, CEIL), pipe_m, r=0.05)
        box("FIT_HANG_BODY_%d" % i, xc - lw/2 - 0.06, xc + lw/2 + 0.06, y - 0.07, y + 0.07, zc - lh/2 - 0.06, zc + lh/2 + 0.06, frm)
        quad("MON_SCR_H%da" % (i + 1), xc - lw/2, xc + lw/2, zc - lh/2, zc + lh/2, y - 0.08, -1, scr); quad("MON_SCR_H%db" % (i + 1), xc - lw/2, xc + lw/2, zc - lh/2, zc + lh/2, y + 0.08, +1, scr)
    return "room: hexes %d, tees %d, screens %d" % (n1, nt, len([o for o in bpy.data.objects if o.name.startswith("MON_SCR_")]))

def export_glb(filename="houston_51.glb"):
    vl = bpy.context.view_layer
    for o in bpy.data.objects:
        try: o.select_set(False)
        except RuntimeError: pass
    KEEP = ("NOLITA_MASSING", "SITE_51", "SITE_W", "SITE_E", "ROADBED", "SIDEWALK", "MEDIAN", "GROUND", "TREES")
    PREFIX = ("ST_", "B51_", "BW_", "BE_", "IN_", "EX_", "FIT_", "MON_")
    n = 0; bpy.context.view_layer.update()
    for o in bpy.data.objects:
        if o.type in ("MESH", "FONT") and (o.name in KEEP or o.name.startswith(PREFIX)) and o.name in vl.objects: o.hide_set(False); o.select_set(True); n += 1
    vl.objects.active = bpy.data.objects["NOLITA_MASSING"]
    path = os.path.join(OUT_DIR, "assets", filename); os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6, export_apply=True, export_cameras=False, export_lights=False, export_yup=True)
    return "exported {} objects {:.0f} KB".format(n, os.path.getsize(path) / 1024)

def points():
    bpy.context.view_layer.update(); r = root(); M = r.matrix_world; o = M @ Vector((0, 0, 0)); ex = M.to_3x3() @ Vector((1, 0, 0)); iw = M.to_3x3() @ Vector((0, 1, 0))
    g = lambda v: [round(v.x, 3), 0, round(-v.y, 3)]
    P = {"room": {"o": [round(o.x, 2), round(o.z, 2), round(-o.y, 2)], "ex": g(ex), "in": g(iw)}, "ft": FT,
         "bwy_laf": [round(v, 1) for v in proj(-73.99543, 40.725605)], "prince_rw": [round(v, 1) for v in proj(-73.9977, 40.72433)], "spring_6": [round(v, 1) for v in proj(-73.99714, 40.7223)],
         "twoav_f": [round(v, 1) for v in proj(-73.98994, 40.7234)], "bowery_jz": [round(v, 1) for v in proj(-73.99391, 40.72028)]}
    return P

if __name__ == "__main__" or bpy.app.background:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for fn in (stage_massing, stage_flat, stage_labels, stage_trees, stage_ground, stage_sites, stage_building, stage_room):
        print(fn(), flush=True)
    P = points(); json.dump(P, open(os.path.join(DATA_DIR, "model_points.json"), "w")); print("points", P, flush=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "houston_51.blend"))
    try: print(export_glb(), flush=True)
    except Exception as e: print("export failed", e, flush=True)
    print("BUILD DONE", flush=True)
