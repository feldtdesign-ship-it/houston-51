"""
render_h51.py: Cycles hero renders of the built-out Long Room, to the standard of the 115 Avenue A heroes (real materials, real cloth, shallow focus, warm light).
Reads build/houston_51_render.blend (made by fitout_render_h51.py). Headless:
  /Applications/Blender.app/Contents/MacOS/Blender --background --python build/render_h51.py -- [quick] [shot ...]
Raw 8-bit PNGs go to renders/raw/<shot>.png; build/post_h51.py adds bloom, grade and grain and writes renders/<shot>.jpg.
Cameras: 24 mm inside (Michael's rule), 35 mm outside. 2560 x 1440 like the 115 heroes.
Look: white-painted brick, pale polished concrete, black paint, oak, the yellow tactile strip, his tees; warm track spots on the work, a cool soft window light from the street.
"""
import bpy, bmesh, math, os, sys
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.dirname(HERE); BLEND = os.path.join(HERE, "houston_51_render.blend")
RAW = os.path.join(OUT, "renders", "raw"); os.makedirs(RAW, exist_ok=True); SCR = os.path.join(HERE, "screens"); FT = 0.3048
# shot: (kind, loc ft, target ft, lens, f-stop, focus ft along the view or None)
SHOTS = {
 "H51_hero_1_long":    ("in", (4.6, 1.2, 4.9),  (6.0, 80.0, 5.0), 24, 4.0, 40.0),
 "H51_hero_2_rail":    ("in", (2.9, 9.0, 4.9),  (10.4, 17.0, 4.5), 24, 2.0, 7.5),
 "H51_hero_3_prints":  ("in", (8.0, 5.0, 5.4),  (1.5, 21.0, 5.2),  24, 3.2, 17.0),
 "H51_hero_4_wall":    ("in", (7.0, 70.8, 5.2), (7.0, 80.1, 5.0),  24, 4.0, 9.5),
 "H51_hero_5_reverse": ("in", (3.0, 77.0, 5.3), (6.0, 1.5, 5.0),   24, 4.0, 40.0),
 "H51_hero_6_galaga":  ("in", (13.5, 70.4, 4.9), (22.4, 77.8, 3.8), 24, 2.2, 12.0),
 "H51_hero_7_tables":  ("in", (5.0, 5.0, 3.4),  (6.5, 40.0, 5.2),  24, 2.8, 10.0),
 "H51_hero_8_street":  ("out", None, None, 50, 5.6, None),
 "H51_doll_found":     ("doll", None, None, 35, 0, None),
 "H51_doll_white":     ("doll", None, None, 35, 0, None),
 "H51_doll_built":     ("doll", None, None, 35, 0, None),
 "H51_plan_built":     ("plan", None, None, 0, 0, None),
}
SHIFT = {"H51_hero_1_long": 0.10, "H51_hero_7_tables": 0.06, "H51_hero_8_street": 0.13}
def root(): return bpy.data.objects["H51_IN"]
def W(x, y, z): return root().matrix_world @ Vector((x * FT, y * FT, z * FT))
def cycles(w, h, samples):
    sc = bpy.context.scene
    try: sc.render.engine = 'CYCLES'
    except TypeError as e: print("engine", e)
    prefs = bpy.context.preferences.addons.get('cycles')
    if prefs:
        cp = prefs.preferences
        for dt in ('METAL', 'CUDA', 'OPTIX', 'NONE'):
            try: cp.compute_device_type = dt; break
            except TypeError: continue
        try:
            cp.get_devices()
            for d in cp.devices: d.use = True
        except Exception as e: print("devices", e)
    sc.cycles.device = 'GPU'; sc.cycles.use_denoising = True; sc.cycles.samples = samples; sc.cycles.max_bounces = 12; sc.cycles.glossy_bounces = 6
    sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
    sc.render.resolution_x = w; sc.render.resolution_y = h; sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_depth = '8'
    for vt in ('AgX', 'Filmic', 'Standard'):
        try: sc.view_settings.view_transform = vt; break
        except TypeError: continue
def P(m): return next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
def srgb(h):
    h = h.lstrip('#'); r, g, b = (int(h[i:i+2], 16) / 255 for i in (0, 2, 4)); f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b), 1)
def fresh(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True
    for n in list(m.node_tree.nodes): m.node_tree.nodes.remove(n)
    return m, m.node_tree.nodes, m.node_tree.links
def setp(b, **kw):
    for k, v in kw.items():
        if k in b.inputs: b.inputs[k].default_value = v
def painted_brick(name, hexc, rough, bump, axis='x'):
    m, n, l = fresh(name); out = n.new('ShaderNodeOutputMaterial'); b = n.new('ShaderNodeBsdfPrincipled'); tc = n.new('ShaderNodeTexCoord'); mp = n.new('ShaderNodeMapping')
    br = n.new('ShaderNodeTexBrick'); nz = n.new('ShaderNodeTexNoise'); bm = n.new('ShaderNodeBump'); mix = n.new('ShaderNodeMath'); mix.operation = 'ADD'
    br.inputs['Scale'].default_value = 1.0; br.inputs['Mortar Size'].default_value = 0.018; br.inputs['Mortar Smooth'].default_value = 0.6; br.inputs['Brick Width'].default_value = 0.21; br.inputs['Row Height'].default_value = 0.068
    br.offset = 0.5; br.offset_frequency = 2; nz.inputs['Scale'].default_value = 90; nz.inputs['Detail'].default_value = 6
    sep = n.new('ShaderNodeSeparateXYZ'); com = n.new('ShaderNodeCombineXYZ'); l.new(tc.outputs['Object'], sep.inputs[0])
    if axis == 'x': l.new(sep.outputs['Y'], com.inputs['X']); l.new(sep.outputs['Z'], com.inputs['Y']); l.new(sep.outputs['X'], com.inputs['Z'])      # walls facing east or west: the courses run along y, up in z
    else: l.new(sep.outputs['X'], com.inputs['X']); l.new(sep.outputs['Z'], com.inputs['Y']); l.new(sep.outputs['Y'], com.inputs['Z'])                    # walls facing the street or the back
    l.new(com.outputs[0], mp.inputs['Vector']); l.new(mp.outputs[0], br.inputs['Vector']); l.new(mp.outputs[0], nz.inputs['Vector']); l.new(br.outputs['Fac'], mix.inputs[0]); l.new(nz.outputs['Fac'], mix.inputs[1])
    bm.inputs['Strength'].default_value = bump; bm.inputs['Distance'].default_value = 0.004; l.new(mix.outputs[0], bm.inputs['Height']); l.new(bm.outputs[0], b.inputs['Normal']); l.new(b.outputs[0], out.inputs[0])
    b.inputs['Base Color'].default_value = srgb(hexc); b.inputs['Roughness'].default_value = rough; return m
def concrete(name, hexc):
    m, n, l = fresh(name); out = n.new('ShaderNodeOutputMaterial'); b = n.new('ShaderNodeBsdfPrincipled'); tc = n.new('ShaderNodeTexCoord'); nz = n.new('ShaderNodeTexNoise'); nz2 = n.new('ShaderNodeTexNoise'); cr = n.new('ShaderNodeMapRange'); bm = n.new('ShaderNodeBump')
    nz.inputs['Scale'].default_value = 2.2; nz.inputs['Detail'].default_value = 8; nz2.inputs['Scale'].default_value = 140; cr.inputs['From Min'].default_value = 0.3; cr.inputs['From Max'].default_value = 0.7; cr.inputs['To Min'].default_value = 0.14; cr.inputs['To Max'].default_value = 0.34
    l.new(tc.outputs['Object'], nz.inputs['Vector']); l.new(tc.outputs['Object'], nz2.inputs['Vector']); l.new(nz.outputs['Fac'], cr.inputs['Value']); l.new(cr.outputs[0], b.inputs['Roughness'])
    bm.inputs['Strength'].default_value = 0.06; l.new(nz2.outputs['Fac'], bm.inputs['Height']); l.new(bm.outputs[0], b.inputs['Normal']); b.inputs['Base Color'].default_value = srgb(hexc); l.new(b.outputs[0], out.inputs[0]); return m
def oak(name):
    m, n, l = fresh(name); out = n.new('ShaderNodeOutputMaterial'); b = n.new('ShaderNodeBsdfPrincipled'); tc = n.new('ShaderNodeTexCoord'); mp = n.new('ShaderNodeMapping'); wv = n.new('ShaderNodeTexWave'); ramp = n.new('ShaderNodeValToRGB'); bm = n.new('ShaderNodeBump')
    mp.inputs['Scale'].default_value = (1, 14, 1); wv.wave_type = 'BANDS'; wv.bands_direction = 'X'; wv.inputs['Scale'].default_value = 7; wv.inputs['Distortion'].default_value = 6; wv.inputs['Detail'].default_value = 3
    ramp.color_ramp.elements[0].color = srgb('#B58A57'); ramp.color_ramp.elements[1].color = srgb('#8A6238')
    l.new(tc.outputs['Object'], mp.inputs['Vector']); l.new(mp.outputs[0], wv.inputs['Vector']); l.new(wv.outputs['Fac'], ramp.inputs['Fac']); l.new(ramp.outputs['Color'], b.inputs['Base Color'])
    bm.inputs['Strength'].default_value = 0.15; l.new(wv.outputs['Fac'], bm.inputs['Height']); l.new(bm.outputs[0], b.inputs['Normal']); b.inputs['Roughness'].default_value = 0.42; l.new(b.outputs[0], out.inputs[0]); return m
def fabric(name, hexc):
    m, n, l = fresh(name); out = n.new('ShaderNodeOutputMaterial'); b = n.new('ShaderNodeBsdfPrincipled'); tc = n.new('ShaderNodeTexCoord'); nz = n.new('ShaderNodeTexNoise'); bm = n.new('ShaderNodeBump')
    nz.inputs['Scale'].default_value = 600; l.new(tc.outputs['Object'], nz.inputs['Vector']); bm.inputs['Strength'].default_value = 0.1; l.new(nz.outputs['Fac'], bm.inputs['Height']); l.new(bm.outputs[0], b.inputs['Normal'])
    b.inputs['Base Color'].default_value = srgb(hexc); b.inputs['Roughness'].default_value = 0.92; setp(b, **{'Sheen Weight': 0.4, 'Sheen Roughness': 0.5}); l.new(b.outputs[0], out.inputs[0]); return m
def emissive(name, path, strength):
    m, n, l = fresh(name); out = n.new('ShaderNodeOutputMaterial'); em = n.new('ShaderNodeEmission'); tex = n.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(path, check_existing=True)
    l.new(tex.outputs['Color'], em.inputs['Color']); em.inputs['Strength'].default_value = strength; l.new(em.outputs[0], out.inputs[0]); return m
def plain(name, hexc, rough):
    m, n, l = fresh(name); out = n.new('ShaderNodeOutputMaterial'); b = n.new('ShaderNodeBsdfPrincipled'); b.inputs['Base Color'].default_value = srgb(hexc); b.inputs['Roughness'].default_value = rough; l.new(b.outputs[0], out.inputs[0]); return m
def assign(prefixes, mat):
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.startswith(prefixes): o.data.materials.clear(); o.data.materials.append(mat)
def realism():
    assign(("IN_WALLE", "IN_WALLW1", "IN_WALLW2", "IN_WALLW3", "IN_HALLWALL", "IN_PARTITION", "IN_WALLX_W", "IN_BATH_E"), painted_brick("real_wall_x", "#E9E6DF", 0.62, 0.55, "x")); assign(("IN_WALLB", "IN_WALLX_B", "IN_WALLW_JOG", "IN_HALLEND", "IN_BATH_FRONT", "IN_BATH_BACK", "IN_BATH_HEAD"), painted_brick("real_wall_y", "#E9E6DF", 0.62, 0.55, "y"))
    assign(("IN_CEIL",), plain("real_ceil", "#F0EEE9", 0.8)); assign(("IN_FLOOR",), concrete("real_floor", "#C9C6BE"))
    assign(("FIT_UNIT_PLANK", "FIT_TBL_TOP"), oak("real_oak"))
    assign(("FIT_UNIT_UP", "FIT_UNIT_ARM", "FIT_UNIT_BRK", "FIT_UNIT_RAIL", "FIT_TBL_LEG", "FIT_GAL_FR", "FIT_MON_FR", "FIT_HANG", "IN_TRACK", "IN_HEAD", "IN_BATHDOOR", "IN_RAD", "BLACK_"), plain("real_black", "#0b0b0c", 0.4))
    tints = {"cream": "#EFE2C6", "navy": "#34496A", "lilac": "#E6CBEA", "moss": "#52635F", "peach": "#F4A887", "black": "#161616", "white": "#F1EFE9"}
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name.startswith("FIT_FOLD") and o.data.materials:
            mt = o.data.materials[0]
            if mt.name.startswith("fit_cw_"): o.data.materials.clear(); o.data.materials.append(fabric("fab_" + mt.name[7:], tints.get(mt.name[7:], "#DDD")))
    m = bpy.data.materials.get("fit_mat")
    if m: P(m).inputs['Roughness'].default_value = 0.95
    for o in bpy.data.objects:
        if o.name.startswith("MON_SCR_"):
            p = os.path.join(SCR, o.name + ".jpg"); o.data.materials.clear()
            if o.name == "MON_SCR_W2": p = os.path.join(OUT, "assets", "art", "nyf_monitor_screen.png")
            if os.path.exists(p): o.data.materials.append(emissive("scr_" + o.name, p, 1.6 if o.name[8] == "B" else 1.3))
    sm, sn, sl = fresh("ada_dots"); so = sn.new('ShaderNodeOutputMaterial'); sb = sn.new('ShaderNodeBsdfPrincipled'); tc = sn.new('ShaderNodeTexCoord'); mp = sn.new('ShaderNodeMapping'); vo = sn.new('ShaderNodeTexVoronoi'); bmp = sn.new('ShaderNodeBump'); mr = sn.new('ShaderNodeMapRange')
    mp.inputs['Scale'].default_value = (1, 1, 0); vo.inputs['Scale'].default_value = 14.0; mr.inputs['From Min'].default_value = 0.0; mr.inputs['From Max'].default_value = 0.42; mr.inputs['To Min'].default_value = 1.0; mr.inputs['To Max'].default_value = 0.0
    sl.new(tc.outputs['Object'], mp.inputs['Vector']); sl.new(mp.outputs[0], vo.inputs['Vector']); sl.new(vo.outputs['Distance'], mr.inputs['Value']); sl.new(mr.outputs[0], bmp.inputs['Height']); bmp.inputs['Strength'].default_value = 0.8; bmp.inputs['Distance'].default_value = 0.004
    sl.new(bmp.outputs[0], sb.inputs['Normal']); sb.inputs['Base Color'].default_value = srgb("#F9D000"); sb.inputs['Roughness'].default_value = 0.5; sl.new(sb.outputs[0], so.inputs[0])
    for o in bpy.data.objects:
        if o.name == "STRIP_SLAB": o.data.materials.clear(); o.data.materials.append(sm)
        if o.name == "STRIP_DOMES": o.hide_render = True
    m = bpy.data.materials.get("ada_yellow")
    if m: b = P(m); b.inputs['Roughness'].default_value = 0.5; b.inputs['Base Color'].default_value = srgb("#F9D400")
    m = bpy.data.materials.get("PJ_SHOPGLASS")
    if m: b = P(m); b.inputs['Alpha'].default_value = 0.06; b.inputs['Roughness'].default_value = 0.02
def clear_lights():
    for o in [o for o in bpy.data.objects if o.type == 'LIGHT' or o.name.startswith("RIG_")]: bpy.data.objects.remove(o, do_unlink=True)
def add_light(name, kind, loc, target, energy, color, size=0.3, spot=None, blend=0.5):
    ld = bpy.data.lights.new(name, kind); ld.energy = energy; ld.color = color
    if kind == 'SPOT': ld.spot_size = math.radians(spot or 40); ld.spot_blend = blend; ld.shadow_soft_size = size
    elif kind == 'AREA': ld.shape = 'RECTANGLE'; ld.size = size[0]; ld.size_y = size[1]
    lo = bpy.data.objects.new("RIG_" + name, ld); bpy.context.scene.collection.objects.link(lo); lo.location = loc
    if target is not None: lo.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return lo
def world(mode):
    sc = bpy.context.scene; w = sc.world or bpy.data.worlds.new("W"); sc.world = w; w.use_nodes = True; nt = w.node_tree
    for n in list(nt.nodes): nt.nodes.remove(n)
    out = nt.nodes.new('ShaderNodeOutputWorld'); bg = nt.nodes.new('ShaderNodeBackground'); nt.links.new(bg.outputs[0], out.inputs[0])
    if mode in ('day', 'dusk'):
        tex = nt.nodes.new('ShaderNodeTexSky')
        try: tex.sky_type = 'NISHITA'; tex.sun_elevation = math.radians(38 if mode == 'day' else -2.5); tex.sun_rotation = math.radians(200); tex.sun_intensity = 0.55; tex.altitude = 10
        except Exception as e: print("sky", e)
        nt.links.new(tex.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = 0.9
    else: bg.inputs[0].default_value = (0.9, 0.9, 0.9, 1); bg.inputs[1].default_value = 1.0
def rig_interior(dusk=False):
    clear_lights(); world('dusk' if dusk else 'day')
    heads = sorted([o for o in bpy.data.objects if o.name.startswith("IN_HEAD_")], key=lambda o: o.name)
    for i, h in enumerate(heads):
        local = root().matrix_world.inverted() @ h.matrix_world.translation; xf, yf = local.x / FT, local.y / FT
        tgt = W(1.5, yf, 5.3) if xf < 6.0 else W(10.4, yf, 3.9)
        add_light("head%02d" % i, 'SPOT', W(xf, yf, 11.0), tgt, 320, (1.0, 0.87, 0.70), 0.05, 26, 0.6)
    for k in range(4): add_light("floorspot%d" % k, 'SPOT', W(6.5, 9.0 + k * 10.0, 11.2), W(6.5, 9.0 + k * 10.0, 0.0), 60, (1.0, 0.9, 0.78), 0.1, 55, 0.7)
    add_light("window", 'AREA', W(6.5, -0.8, 5.2), W(6.5, 14.0, 3.5), 700, (0.86, 0.92, 1.0), (7 * FT, 8 * FT))
    add_light("cove", 'AREA', W(6.5, 20.0, 11.3), W(6.5, 20.0, 0.0), 170, (1.0, 0.92, 0.82), (6 * FT, 40 * FT))
    for k, xx in enumerate((5.0, 12.0, 19.0)): add_light("ext%d" % k, 'SPOT', W(xx, 74.0, 8.9), W(xx, 74.0, 0.0), 320, (1.0, 0.92, 0.82), 0.08, 70, 0.6)
    add_light("ext_fill", 'AREA', W(13.0, 74.0, 8.9), W(13.0, 74.0, 0.0), 260, (1.0, 0.92, 0.82), (20 * FT, 8 * FT))
    add_light("bath_passage", 'AREA', W(3.3, 56.0, 9.3), W(3.3, 56.0, 0.0), 90, (1.0, 0.92, 0.82), (2.5 * FT, 14 * FT))
def set_visibility(kind, ex, fit):
    for o in bpy.data.objects:
        n = o.name
        if n.startswith("EX_"): o.hide_render = not ex
        elif n.startswith(("FIT_", "MON_", "STRIP_", "BLACK_", "RTEE_", "galaga")): o.hide_render = not fit
    for n in ("SITE_51", "SITE_W", "SITE_E"):
        o = bpy.data.objects.get(n)
        if o: o.hide_render = kind in ("in", "doll", "plan")
    for o in bpy.data.objects:
        if o.name.startswith(("B51_", "BW_", "BE_")) and o.type == 'MESH': o.hide_render = kind in ("doll", "plan")
        if o.name.startswith(("IN_CEIL", "IN_TRACK", "IN_HEAD")): o.hide_render = kind in ("doll", "plan")
        if o.name in ("NOLITA_MASSING", "TREES") or o.name.startswith("ST_"): o.hide_render = kind in ("doll", "plan")
        if o.name.startswith("IN_WALLW"): o.hide_render = kind in ("doll", "plan")
def cam(name, loc, target, lens, fstop=0, focus_ft=None, ortho=None, rot=None):
    c = bpy.data.objects.get(name)
    if not c: c = bpy.data.objects.new(name, bpy.data.cameras.new(name)); bpy.context.scene.collection.objects.link(c)
    c.location = loc; d = c.data; d.lens = lens; d.clip_end = 3000; d.clip_start = 0.05; d.shift_y = SHIFT.get(name, 0.0)
    if ortho: d.type = 'ORTHO'; d.ortho_scale = ortho
    c.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    if rot is not None: c.rotation_euler = rot
    d.dof.use_dof = bool(fstop and focus_ft)
    if d.dof.use_dof: d.dof.aperture_fstop = fstop; d.dof.focus_distance = focus_ft * FT
    return c
def brick_facade(name, c1, c2, mortar, ang, bump=0.7):
    """triplanar-ish brick for the Houston fronts: the world is rotated into the facade's frame so courses run level, then front/back faces use the xz plane and side faces the yz plane"""
    m, n, l = fresh(name); out = n.new('ShaderNodeOutputMaterial'); b = n.new('ShaderNodeBsdfPrincipled'); tc = n.new('ShaderNodeTexCoord'); mp = n.new('ShaderNodeMapping'); sep = n.new('ShaderNodeSeparateXYZ')
    mp.inputs['Rotation'].default_value = (0, 0, -ang); l.new(tc.outputs['Object'], mp.inputs['Vector']); l.new(mp.outputs[0], sep.inputs[0])
    nrm = n.new('ShaderNodeNewGeometry'); mapn = n.new('ShaderNodeMapping'); mapn.inputs['Rotation'].default_value = (0, 0, -ang); mapn.vector_type = 'VECTOR'
    # normal in object space is not exposed; use the geometry normal in world space, rotated the same way
    l.new(nrm.outputs['Normal'], mapn.inputs['Vector']); sn = n.new('ShaderNodeSeparateXYZ'); l.new(mapn.outputs[0], sn.inputs[0])
    ax = n.new('ShaderNodeMath'); ax.operation = 'ABSOLUTE'; l.new(sn.outputs['X'], ax.inputs[0]); ay = n.new('ShaderNodeMath'); ay.operation = 'ABSOLUTE'; l.new(sn.outputs['Y'], ay.inputs[0])
    wx = n.new('ShaderNodeMath'); wx.operation = 'POWER'; wx.inputs[1].default_value = 6.0; l.new(ax.outputs[0], wx.inputs[0])
    def brick_on(u, v):
        cb = n.new('ShaderNodeCombineXYZ'); l.new(u, cb.inputs['X']); l.new(v, cb.inputs['Y']); br = n.new('ShaderNodeTexBrick')
        br.inputs['Color1'].default_value = srgb(c1); br.inputs['Color2'].default_value = srgb(c2); br.inputs['Mortar'].default_value = srgb(mortar); br.inputs['Scale'].default_value = 1.0
        br.inputs['Mortar Size'].default_value = 0.012; br.inputs['Mortar Smooth'].default_value = 0.4; br.inputs['Brick Width'].default_value = 0.21; br.inputs['Row Height'].default_value = 0.068; br.inputs['Bias'].default_value = 0.0; br.offset = 0.5; br.offset_frequency = 2
        l.new(cb.outputs[0], br.inputs['Vector']); return br
    b_xz = brick_on(sep.outputs['X'], sep.outputs['Z']); b_yz = brick_on(sep.outputs['Y'], sep.outputs['Z'])
    mixc = n.new('ShaderNodeMix'); mixc.data_type = 'RGBA'; l.new(wx.outputs[0], mixc.inputs[0]); l.new(b_xz.outputs['Color'], mixc.inputs[6]); l.new(b_yz.outputs['Color'], mixc.inputs[7])
    mixf = n.new('ShaderNodeMix'); mixf.data_type = 'FLOAT'; l.new(wx.outputs[0], mixf.inputs[0]); l.new(b_xz.outputs['Fac'], mixf.inputs[2]); l.new(b_yz.outputs['Fac'], mixf.inputs[3])
    bm = n.new('ShaderNodeBump'); bm.inputs['Strength'].default_value = bump; bm.inputs['Distance'].default_value = 0.01; l.new(mixf.outputs[0], bm.inputs['Height']); l.new(bm.outputs[0], b.inputs['Normal'])
    l.new(mixc.outputs[2], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.88; l.new(b.outputs[0], out.inputs[0]); return m
def street_realism():
    import math as _m
    ang = _m.atan2(root().matrix_world.to_3x3()[1][0], root().matrix_world.to_3x3()[0][0])
    assign(("SITE_51", "B51_HOUSTON_BRICK"), brick_facade("st_brick51", "#8A5443", "#9B6450", "#B3ADA2", ang))
    assign(("SITE_W", "BW_"), brick_facade("st_brickW", "#A58A66", "#B79B76", "#B3ADA2", ang)); assign(("SITE_E", "BE_"), brick_facade("st_brickE", "#C9BA98", "#D6C8A6", "#B3ADA2", ang))
    for o in bpy.data.objects:      # the black ironwork stays black; trim and stone stay light
        if o.name.startswith(("B51_HOUSTON_IRON", "BW_HOUSTON_IRON", "BE_HOUSTON_IRON")): o.data.materials.clear(); o.data.materials.append(plain("st_iron", "#0b0b0c", 0.35))
        if o.name.startswith(("B51_HOUSTON_TRIM", "BW_HOUSTON_TRIM", "BE_HOUSTON_TRIM", "B51_HOUSTON_STONE")): o.data.materials.clear(); o.data.materials.append(plain("st_trim", "#CFC9BC", 0.7))
        if ("_GLASS" in o.name and o.name.startswith(("B51_", "BW_", "BE_")) and "SHOP" not in o.name) or ("SHOPGLASS" in o.name and o.name.startswith(("BW_", "BE_"))):
            gm, gn, gl = fresh("st_glass"); go = gn.new('ShaderNodeOutputMaterial'); gb = gn.new('ShaderNodeBsdfPrincipled'); gb.inputs['Base Color'].default_value = srgb("#0f1a22"); gb.inputs['Roughness'].default_value = 0.03; setp(gb, **{'Specular IOR Level': 0.8}); gl.new(gb.outputs[0], go.inputs[0]); o.data.materials.clear(); o.data.materials.append(gm)
    # sidewalk: concrete with slab joints; road: asphalt
    sw, sn, sl = fresh("st_walk"); so = sn.new('ShaderNodeOutputMaterial'); sb = sn.new('ShaderNodeBsdfPrincipled'); tc = sn.new('ShaderNodeTexCoord'); br = sn.new('ShaderNodeTexBrick'); nz = sn.new('ShaderNodeTexNoise'); bm = sn.new('ShaderNodeBump')
    br.inputs['Scale'].default_value = 1.0; br.inputs['Brick Width'].default_value = 1.5; br.inputs['Row Height'].default_value = 1.5; br.inputs['Mortar Size'].default_value = 0.012; br.inputs['Color1'].default_value = srgb("#B9B6AE"); br.inputs['Color2'].default_value = srgb("#AFACA4"); br.inputs['Mortar'].default_value = srgb("#6E6C66"); nz.inputs['Scale'].default_value = 60
    sl.new(tc.outputs['Object'], br.inputs['Vector']); sl.new(tc.outputs['Object'], nz.inputs['Vector']); sl.new(br.outputs['Color'], sb.inputs['Base Color']); sl.new(nz.outputs['Fac'], bm.inputs['Height']); bm.inputs['Strength'].default_value = 0.15; sl.new(bm.outputs[0], sb.inputs['Normal']); sb.inputs['Roughness'].default_value = 0.85; sl.new(sb.outputs[0], so.inputs[0]); assign(("SIDEWALK",), sw)
    rd, rn, rl = fresh("st_road"); ro = rn.new('ShaderNodeOutputMaterial'); rb = rn.new('ShaderNodeBsdfPrincipled'); rtc = rn.new('ShaderNodeTexCoord'); rnz = rn.new('ShaderNodeTexNoise'); rbm = rn.new('ShaderNodeBump'); rcr = rn.new('ShaderNodeValToRGB')
    rnz.inputs['Scale'].default_value = 25; rnz.inputs['Detail'].default_value = 10; rcr.color_ramp.elements[0].color = srgb("#1d1e20"); rcr.color_ramp.elements[1].color = srgb("#34363a")
    rl.new(rtc.outputs['Object'], rnz.inputs['Vector']); rl.new(rnz.outputs['Fac'], rcr.inputs['Fac']); rl.new(rcr.outputs['Color'], rb.inputs['Base Color']); rl.new(rnz.outputs['Fac'], rbm.inputs['Height']); rbm.inputs['Strength'].default_value = 0.2; rl.new(rbm.outputs[0], rb.inputs['Normal']); rb.inputs['Roughness'].default_value = 0.6; rl.new(rb.outputs[0], ro.inputs[0]); assign(("ROADBED",), rd)
    # PJ's signature in white on the black sign band, lit
    sm, sn2, sl2 = fresh("st_sig"); sout = sn2.new('ShaderNodeOutputMaterial'); stex = sn2.new('ShaderNodeTexImage'); stex.image = bpy.data.images.load(os.path.join(OUT, "assets", "pj_sig_white.png"), check_existing=True)
    sem = sn2.new('ShaderNodeEmission'); strn = sn2.new('ShaderNodeBsdfTransparent'); smix = sn2.new('ShaderNodeMixShader'); sem.inputs['Strength'].default_value = 3.0
    sl2.new(stex.outputs['Color'], sem.inputs['Color']); sl2.new(stex.outputs['Alpha'], smix.inputs[0]); sl2.new(strn.outputs[0], smix.inputs[1]); sl2.new(sem.outputs[0], smix.inputs[2]); sl2.new(smix.outputs[0], sout.inputs[0])
    wdt = 5.2; hgt = wdt * stex.image.size[1] / max(1, stex.image.size[0]); xc, zc, yy = 6.46, 10.5, -0.97
    bm2 = bmesh.new(); pts = [((xc - wdt / 2, yy, zc - hgt / 2), (0, 0)), ((xc + wdt / 2, yy, zc - hgt / 2), (1, 0)), ((xc + wdt / 2, yy, zc + hgt / 2), (1, 1)), ((xc - wdt / 2, yy, zc + hgt / 2), (0, 1))]
    vs = [bm2.verts.new((p[0] * FT, p[1] * FT, p[2] * FT)) for p, _ in pts]; fc = bm2.faces.new(vs); uv = bm2.loops.layers.uv.new()
    for loop, (_, t) in zip(fc.loops, pts): loop[uv].uv = t
    me = bpy.data.meshes.new("st_sigplane"); bm2.to_mesh(me); bm2.free(); so_ = bpy.data.objects.new("ST_SIG", me); bpy.context.scene.collection.objects.link(so_); so_.parent = root(); so_.data.materials.append(sm)
def render(shot, w, h, samples):
    kind, loc, tgt, lens, fstop, focus = SHOTS[shot]; sc = bpy.context.scene; 
    if kind == 'plan': w, h = 1500, 2000
    cycles(w, h, samples); sc.view_settings.exposure = -0.5
    if kind == "in":
        set_visibility(kind, False, True); rig_interior(); c = cam(shot, W(*loc), W(*tgt), lens, fstop, focus)
    elif kind == "out":
        set_visibility(kind, False, True); rig_interior(dusk=True); sc.view_settings.exposure = -0.3
        for o in bpy.data.objects:
            if o.name == 'TREES' or o.name.startswith('ST_') and o.name != 'ST_SIG': o.hide_render = True
            if o.type == 'LIGHT' or o.name.startswith('RIG_'):
                try: o.data.energy *= 0.30
                except Exception: pass
        bpy.data.objects['RIG_window'].data.energy = 0
        street_realism(); add_light("street_fill", 'AREA', W(-6.0, -70.0, 12.0), W(6.5, 0.0, 7.0), 2200, (1.0, 0.78, 0.55), (14 * FT, 8 * FT))
        c = cam(shot, W(-6.0, -74.0, 5.6), W(6.2, 0.0, 6.8), lens, fstop, 76.0)
    elif kind == "doll":
        set_visibility(kind, shot.endswith("found"), shot.endswith("built")); clear_lights(); world('flat')
        if shot.endswith("white"):
            for o in bpy.data.objects:
                if o.name.startswith("IN_WALLW"): o.hide_render = True
        add_light("sun", 'SUN', (0, 0, 100), None, 3.2, (1, 0.97, 0.92)); bpy.data.objects["RIG_sun"].rotation_euler = (math.radians(48), math.radians(8), math.radians(-35)); bpy.data.lights["sun"].angle = math.radians(2.0)
        c = cam(shot, W(38, -28, 70), W(9, 42, 3), lens)
    else:
        set_visibility(kind, False, True); clear_lights(); world('flat'); add_light("sun", 'SUN', (0, 0, 100), None, 3.2, (1, 0.97, 0.92)); bpy.data.objects["RIG_sun"].rotation_euler = (math.radians(30), 0, math.radians(-20)); bpy.data.lights["sun"].angle = math.radians(3.0)
        iv = root().matrix_world.to_3x3() @ Vector((0, 1, 0)); th = math.atan2(-iv.x, iv.y); c = cam(shot, W(11.0, 41.0, 90.0), W(11.0, 41.0, 0.0), 0, ortho=90 * FT, rot=(0, 0, th))
    sc.camera = c; sc.render.filepath = os.path.join(RAW, shot + ".png"); bpy.ops.render.render(write_still=True); return "rendered " + shot
if bpy.app.background:
    bpy.ops.wm.open_mainfile(filepath=BLEND); realism()
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    quick = "quick" in args; names = [a for a in args if a in SHOTS] or list(SHOTS)
    for s in names:
        try: print(render(s, 1280 if quick else 2560, 720 if quick else 1440, 40 if quick else 192), flush=True)
        except Exception as e: print("render failed", s, repr(e), flush=True)
    print("RENDERS DONE", flush=True)
