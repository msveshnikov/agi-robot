"""
NOVA rover - procedural Blender model of the AGI robot (redesign v2).

All geometry is built in millimetres under a root empty scaled 0.001, so the
world size is real (about 205 x 132 x 112 mm when parked).

Axes: +Y = front, +X = right, +Z = up, ground at z = 0.

Hardware this shell is designed around (same as the current robot):
  * 2 x SG90 continuous servos  -> drive wheels (D11 left, D10 right)
  * 2 x SG90 180 servos         -> arm shoulder (D4) and elbow (D7)
  * Arduino Uno Q, 10000 mAh power bank, HC-SR04, USB webcam, mini speaker,
    RGB LED (lights the translucent "mood ring"), Modulino Thermo.

Arm joint convention (matches python/main.py arm1 / arm2):
  arm1 (shoulder) 0 = folded back, lying in the roof bay; 90 = straight up;
                  180 = pointing straight forward.
  arm2 (elbow)    180 = straight; 90 = forearm at right angle (pointing at the
                  floor when arm1 = 180); smaller = folded further.
"""
import bpy
import bmesh
import math
from mathutils import Vector, Matrix

# ---------------------------------------------------------------- dimensions
BODY_A = 58.0        # half width of body
BODY_BF = 100.0      # front half length
BODY_BB = 96.0       # rear half length
Z_BOTTOM = 5.0
Z_TUB_TOP = 48.0
Z_CAN_BOT = 52.0
Z_TOP = 94.0
WHEEL_R = 36.0
WHEEL_W = 18.0
WHEEL_X = 56.0
AXLE_Z = 36.0
AXLE_Y = 0.0
SHOULDER = Vector((0.0, 58.0, 102.0))
L1 = 55.0
L2 = 88.0
BAY_FLOOR = 88.0


# ================================================================== helpers
def link_obj(obj, coll):
    coll.objects.link(obj)
    return obj


def new_mesh_obj(name, coll, verts=None, faces=None, bm=None):
    me = bpy.data.meshes.new(name)
    if bm is not None:
        bm.to_mesh(me)
        bm.free()
    else:
        me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def smooth_by_angle(ob, angle_deg=35.0):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    a = math.radians(angle_deg)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        if len(e.link_faces) == 2:
            e.smooth = e.calc_face_angle(0.0) < a
        else:
            e.smooth = False
    bm.to_mesh(ob.data)
    bm.free()


def apply_mods(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev)
    old = ob.data
    ob.modifiers.clear()
    ob.data = me
    if old.users == 0:
        bpy.data.meshes.remove(old)


def boolean(ob, cutter, op='DIFFERENCE', keep=False):
    m = ob.modifiers.new("bool", 'BOOLEAN')
    m.operation = op
    m.solver = 'EXACT'
    m.object = cutter
    m.use_self = True
    m.use_hole_tolerant = True
    apply_mods(ob)
    if not keep:
        bpy.data.objects.remove(cutter, do_unlink=True)


def bevel(ob, width, segs=4, angle=40.0):
    m = ob.modifiers.new("bev", 'BEVEL')
    m.width = width
    m.segments = segs
    m.limit_method = 'ANGLE'
    m.angle_limit = math.radians(angle)
    m.harden_normals = False
    apply_mods(ob)


def subsurf(ob, levels=2):
    m = ob.modifiers.new("sub", 'SUBSURF')
    m.levels = levels
    m.render_levels = levels
    apply_mods(ob)


def prim_cube(name, coll, size, loc):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2])) + Vector(loc)
    return new_mesh_obj(name, coll, bm=bm)


def rounded_box(name, coll, size, loc, radius, segs=5):
    ob = prim_cube(name, coll, size, loc)
    bevel(ob, radius, segs, 30)
    return ob


def prim_cyl(name, coll, r, depth, loc, axis='Z', segs=64, r2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segs,
                          radius1=r, radius2=r if r2 is None else r2, depth=depth)
    rot = {'Z': Matrix.Identity(4),
           'X': Matrix.Rotation(math.radians(90), 4, 'Y'),
           'Y': Matrix.Rotation(math.radians(90), 4, 'X')}[axis]
    bmesh.ops.transform(bm, matrix=Matrix.Translation(Vector(loc)) @ rot, verts=bm.verts)
    return new_mesh_obj(name, coll, bm=bm)


def prim_sphere(name, coll, r, loc, segs=48, rings=24):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings, radius=r)
    bmesh.ops.translate(bm, vec=Vector(loc), verts=bm.verts)
    return new_mesh_obj(name, coll, bm=bm)


def prim_torus(name, coll, R, r, loc, axis='Y', segs=64, rsegs=16):
    verts, faces = [], []
    for i in range(segs):
        u = 2 * math.pi * i / segs
        for j in range(rsegs):
            v = 2 * math.pi * j / rsegs
            p = Vector(((R + r * math.cos(v)) * math.cos(u), (R + r * math.cos(v)) * math.sin(u), r * math.sin(v)))
            verts.append(p)
    for i in range(segs):
        for j in range(rsegs):
            a = i * rsegs + j
            b = ((i + 1) % segs) * rsegs + j
            c = ((i + 1) % segs) * rsegs + (j + 1) % rsegs
            d = i * rsegs + (j + 1) % rsegs
            faces.append((a, b, c, d))
    rot = {'Z': Matrix.Identity(3), 'X': Matrix.Rotation(math.radians(90), 3, 'Y'),
           'Y': Matrix.Rotation(math.radians(90), 3, 'X')}[axis]
    verts = [rot @ v + Vector(loc) for v in verts]
    ob = new_mesh_obj(name, coll, verts, faces)
    smooth_by_angle(ob, 80)
    return ob


def hull_obj(name, coll, points):
    bm = bmesh.new()
    for p in points:
        bm.verts.new(p)
    res = bmesh.ops.convex_hull(bm, input=bm.verts[:])
    # drop interior points that were not used
    unused = [v for v in res.get("geom_unused", []) if isinstance(v, bmesh.types.BMVert)]
    bmesh.ops.delete(bm, geom=unused, context='VERTS')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    ob = new_mesh_obj(name, coll, bm=bm)
    return ob


def capsule_x_points(center, half_len, r, fillet, n=40, m=6):
    """Points of a cylinder along X with filleted rims (for convex hulls)."""
    pts = []
    cx, cy, cz = center
    for k in range(m + 1):
        t = (math.pi / 2) * k / m
        xr = half_len - fillet + fillet * math.sin(t)
        rr = r - fillet + fillet * math.cos(t)
        for sgn in (-1, 1):
            for i in range(n):
                a = 2 * math.pi * i / n
                pts.append(Vector((cx + sgn * xr, cy + rr * math.cos(a), cz + rr * math.sin(a))))
    return pts


def solidify_copy(ob, thickness):
    m = ob.modifiers.new("solid", 'SOLIDIFY')
    m.thickness = thickness
    m.offset = -1.0
    m.use_even_offset = True
    m.use_quality_normals = True
    apply_mods(ob)


# ============================================================== body shape
def profile(z, inset=0.0, part='body'):
    """Return (a, bf, bb, n) of the superellipse cross-section at height z."""
    a, bf, bb = BODY_A, BODY_BF, BODY_BB
    n = 4.0
    ins = 0.0
    if z < 17.0:                        # rounded belly
        d = (17.0 - z) / 12.0
        ins = 12.0 * (1.0 - math.sqrt(max(0.0, 1.0 - d * d)))
    elif z <= Z_TUB_TOP + 4.0:          # slight waist bulge
        a += 1.2 * math.sin(math.pi * (z - 17.0) / 35.0)
    if z > 50.0:                        # canopy taper + visor rake
        u = (z - 50.0) / (Z_TOP - 50.0)
        a = BODY_A - 12.0 * u ** 1.6
        bf = BODY_BF - 30.0 * u ** 1.3
        bb = BODY_BB - 12.0 * u ** 1.8
        n = 4.0 - 0.8 * u
        if z > Z_TOP - 10.0:
            d = (z - (Z_TOP - 10.0)) / 10.0
            ins = 10.0 * (1.0 - math.sqrt(max(0.0, 1.0 - d * d)))
    ins += inset
    return a - ins, bf - ins, bb - ins, n


def ring_points(z, a, bf, bb, n, segs):
    pts = []
    for i in range(segs):
        th = 2 * math.pi * i / segs
        c, s = math.cos(th), math.sin(th)
        x = a * math.copysign(abs(c) ** (2.0 / n), c)
        yy = math.copysign(abs(s) ** (2.0 / n), s)
        y = yy * (bf if s > 0 else bb)
        pts.append(Vector((x, y, z)))
    return pts


def loft_body(name, coll, z0, z1, inset=0.0, segs=160, steps=None):
    zs = []
    if steps is None:
        steps = max(4, int((z1 - z0) / 1.2))
    for k in range(steps + 1):
        t = k / steps
        # cluster rings near the rounded ends
        zs.append(z0 + (z1 - z0) * t)
    verts, faces = [], []
    for z in zs:
        a, bf, bb, n = profile(z, inset)
        a = max(a, 0.5)
        bf = max(bf, 0.5)
        bb = max(bb, 0.5)
        verts += ring_points(z, a, bf, bb, n, segs)
    R = len(zs)
    for r in range(R - 1):
        for i in range(segs):
            a0 = r * segs + i
            a1 = r * segs + (i + 1) % segs
            b1 = (r + 1) * segs + (i + 1) % segs
            b0 = (r + 1) * segs + i
            faces.append((a0, a1, b1, b0))
    # caps
    bc = len(verts)
    verts.append(Vector((0, (profile(z0, inset)[1] - profile(z0, inset)[2]) * 0.0, z0)))
    tc = len(verts)
    verts.append(Vector((0, 0, z1)))
    for i in range(segs):
        faces.append((bc, (i + 1) % segs, i))
        faces.append((tc, (R - 1) * segs + i, (R - 1) * segs + (i + 1) % segs))
    ob = new_mesh_obj(name, coll, verts, faces)
    smooth_by_angle(ob, 60)
    return ob


# ================================================================ materials
def _principled(mat):
    return next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')


def _set(bsdf, key, val):
    if key in bsdf.inputs:
        bsdf.inputs[key].default_value = val


def layer_lines(mat, strength=0.06, pitch=0.2):
    """Subtle FDM layer lines: bump from object-space Z (object units = mm)."""
    nt = mat.node_tree
    bsdf = _principled(mat)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    mul = nt.nodes.new('ShaderNodeMath')
    mul.operation = 'MULTIPLY'
    mul.inputs[1].default_value = 2 * math.pi / pitch
    sn = nt.nodes.new('ShaderNodeMath')
    sn.operation = 'SINE'
    ab = nt.nodes.new('ShaderNodeMath')
    ab.operation = 'ABSOLUTE'
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = strength
    bump.inputs['Distance'].default_value = 0.02
    nt.links.new(tc.outputs['Object'], sep.inputs[0])
    nt.links.new(sep.outputs['Z'], mul.inputs[0])
    nt.links.new(mul.outputs[0], sn.inputs[0])
    nt.links.new(sn.outputs[0], ab.inputs[0])
    nt.links.new(ab.outputs[0], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])


def make_mat(name, color, rough=0.4, metal=0.0, coat=0.0, emis=None, emis_str=0.0,
             trans=0.0, ior=1.45, sss=0.0, lines=False, alpha=1.0, spec=0.5):
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    b = _principled(mat)
    _set(b, 'Base Color', (*color, 1.0))
    _set(b, 'Roughness', rough)
    _set(b, 'Metallic', metal)
    _set(b, 'Coat Weight', coat)
    _set(b, 'Coat Roughness', 0.08)
    _set(b, 'Transmission Weight', trans)
    _set(b, 'IOR', ior)
    _set(b, 'Specular IOR Level', spec)
    if sss > 0:
        _set(b, 'Subsurface Weight', sss)
        _set(b, 'Subsurface Radius', (1.0, 0.9, 0.8))
        _set(b, 'Subsurface Scale', 0.6)
    if emis is not None:
        _set(b, 'Emission Color', (*emis, 1.0))
        _set(b, 'Emission Strength', emis_str)
    if alpha < 1.0:
        _set(b, 'Alpha', alpha)
    mat.diffuse_color = (*color, 1.0)
    if lines:
        layer_lines(mat)
    return mat


def make_materials():
    M = {}
    M['white'] = make_mat('PLA_Pearl', (0.82, 0.83, 0.85), rough=0.32, coat=0.15, sss=0.04, lines=True)
    M['graphite'] = make_mat('PLA_Graphite', (0.028, 0.03, 0.034), rough=0.42, lines=True)
    M['orange'] = make_mat('PLA_Orange', (0.95, 0.24, 0.02), rough=0.35, lines=True)
    M['visor'] = make_mat('Visor_Gloss', (0.004, 0.005, 0.007), rough=0.06, coat=1.0, spec=0.7)
    M['tpu'] = make_mat('TPU_Black', (0.018, 0.018, 0.02), rough=0.75)
    M['alu'] = make_mat('Aluminium', (0.8, 0.8, 0.82), rough=0.28, metal=1.0)
    M['steel'] = make_mat('Steel', (0.6, 0.6, 0.62), rough=0.2, metal=1.0)
    M['lens'] = make_mat('Lens_Glass', (0.02, 0.03, 0.06), rough=0.0, coat=1.0, spec=1.0)
    M['servo'] = make_mat('Servo_Blue', (0.02, 0.08, 0.5), rough=0.4)
    M['pcb'] = make_mat('PCB_Blue', (0.02, 0.15, 0.38), rough=0.35)
    M['pcb_green'] = make_mat('PCB_Green', (0.02, 0.2, 0.06), rough=0.35)
    M['battery'] = make_mat('Battery_Alu', (0.12, 0.12, 0.13), rough=0.3, metal=0.8)
    # mood ring: translucent PETG lit by the RGB LED. Emission colour is animated.
    glow = make_mat('Glow_Ring', (0.85, 0.95, 1.0), rough=0.25, trans=0.6,
                    emis=(0.1, 0.85, 1.0), emis_str=12.0)
    M['glow'] = glow
    M['eye_glow'] = make_mat('Eye_Glow', (0.9, 0.95, 1.0), rough=0.3,
                             emis=(0.1, 0.85, 1.0), emis_str=18.0)
    M['led_matrix'] = make_led_matrix_mat()
    M['grille'] = make_mat('Grille_Dark', (0.01, 0.01, 0.012), rough=0.6)
    return M


def make_led_matrix_mat():
    """Smoked window over the Uno Q 13x8 LED matrix - dot grid via object coords."""
    name = 'LED_Matrix'
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    b = _principled(mat)
    _set(b, 'Base Color', (0.004, 0.004, 0.006, 1))
    _set(b, 'Roughness', 0.08)
    _set(b, 'Coat Weight', 1.0)
    _set(b, 'Emission Color', (1.0, 0.25, 0.05, 1))
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs[0])

    def cell(axis_out, pitch):
        m = nt.nodes.new('ShaderNodeMath'); m.operation = 'DIVIDE'; m.inputs[1].default_value = pitch
        f = nt.nodes.new('ShaderNodeMath'); f.operation = 'FRACT'
        s = nt.nodes.new('ShaderNodeMath'); s.operation = 'SUBTRACT'; s.inputs[1].default_value = 0.5
        a = nt.nodes.new('ShaderNodeMath'); a.operation = 'ABSOLUTE'
        nt.links.new(sep.outputs[axis_out], m.inputs[0]); nt.links.new(m.outputs[0], f.inputs[0])
        nt.links.new(f.outputs[0], s.inputs[0]); nt.links.new(s.outputs[0], a.inputs[0])
        return a, m
    ax, mx = cell('X', 2.4)
    ay, my = cell('Y', 2.4)
    mx_ = nt.nodes.new('ShaderNodeMath'); mx_.operation = 'MAXIMUM'
    nt.links.new(ax.outputs[0], mx_.inputs[0]); nt.links.new(ay.outputs[0], mx_.inputs[1])
    lt = nt.nodes.new('ShaderNodeMath'); lt.operation = 'LESS_THAN'; lt.inputs[1].default_value = 0.22
    nt.links.new(mx_.outputs[0], lt.inputs[0])
    # pseudo random "on" pattern per cell (animated via mapping W input)
    fl1 = nt.nodes.new('ShaderNodeMath'); fl1.operation = 'FLOOR'
    fl2 = nt.nodes.new('ShaderNodeMath'); fl2.operation = 'FLOOR'
    nt.links.new(mx.outputs[0], fl1.inputs[0]); nt.links.new(my.outputs[0], fl2.inputs[0])
    comb = nt.nodes.new('ShaderNodeCombineXYZ')
    nt.links.new(fl1.outputs[0], comb.inputs[0]); nt.links.new(fl2.outputs[0], comb.inputs[1])
    wn = nt.nodes.new('ShaderNodeTexWhiteNoise')
    wn.noise_dimensions = '4D'
    wn.name = 'MatrixNoise'
    nt.links.new(comb.outputs[0], wn.inputs['Vector'])
    gt = nt.nodes.new('ShaderNodeMath'); gt.operation = 'GREATER_THAN'; gt.inputs[1].default_value = 0.55
    nt.links.new(wn.outputs['Value'], gt.inputs[0])
    on = nt.nodes.new('ShaderNodeMath'); on.operation = 'MULTIPLY'
    nt.links.new(lt.outputs[0], on.inputs[0]); nt.links.new(gt.outputs[0], on.inputs[1])
    st = nt.nodes.new('ShaderNodeMath'); st.operation = 'MULTIPLY'; st.inputs[1].default_value = 25.0
    st.name = 'MatrixStrength'
    nt.links.new(on.outputs[0], st.inputs[0])
    nt.links.new(st.outputs[0], b.inputs['Emission Strength'])
    return mat


def set_mat(ob, mat):
    ob.data.materials.clear()
    ob.data.materials.append(mat)


# ============================================================ build pieces
class Robot:
    pass


def build_body(coll, M, R):
    # ---------------- tub (lower shell, graphite)
    tub = loft_body('Tub', coll, Z_BOTTOM, Z_TUB_TOP)
    ring = loft_body('MoodRing', coll, Z_TUB_TOP - 0.5, Z_CAN_BOT + 0.5, inset=1.4, steps=6)
    can = loft_body('Canopy', coll, Z_CAN_BOT, Z_TOP)

    # wheel arches (both sides) - cut into tub, ring and canopy
    for ob in (tub, ring, can):
        for sx in (-1, 1):
            cut = prim_cyl('arch', coll, WHEEL_R + 5.0, 60, (sx * (43.0 + 30), AXLE_Y, AXLE_Z), 'X', 96)
            boolean(ob, cut)

    # visor opening in canopy + visor panel
    vcut = rounded_box('visorcut', coll, (82, 80, 30), (0, 100, 71), 9, 6)
    can_inset = loft_body('VisorSrc', coll, Z_CAN_BOT, Z_TOP, inset=0.9)
    boolean(can, vcut, keep=True)
    boolean(can_inset, vcut, op='INTERSECT', keep=False)
    visor = can_inset
    visor.name = 'Visor'
    # eye + camera holes in visor
    for sx in (-1, 1):
        boolean(visor, prim_cyl('eyehole', coll, 9.0, 40, (sx * 13.0, 95, 66), 'Y', 64))
    boolean(visor, prim_cyl('camhole', coll, 5.0, 40, (0, 85, 80.5), 'Y', 48))

    # roof arm bay (recessed channel)
    bay = rounded_box('baycut', coll, (54, 150, 30), (0, -15, BAY_FLOOR + 15), 6, 5)
    boolean(can, bay)
    tray = rounded_box('BayTray', coll, (53.2, 148, 4), (0, -15, BAY_FLOOR - 1.4), 1.0, 3)
    clip = loft_body('trayclip', coll, Z_CAN_BOT, Z_TOP + 10, inset=0.6)
    boolean(tray, clip, op='INTERSECT')

    # LED matrix window in the bay floor (visible when arm deployed)
    win = rounded_box('MatrixWindow', coll, (34, 22, 1.2), (0, -30, BAY_FLOOR + 0.5), 2.5, 4)

    # rear speaker grille (hex holes through the tub)
    holes = []
    hr = 2.0
    for row in range(5):
        for col in range(-6, 7):
            x = col * 4.8 + (2.4 if row % 2 else 0)
            z = 22 + row * 4.2
            if abs(x) > 28:
                continue
            holes.append(prim_cyl('h', coll, hr, 30, (x, -96, z), 'Y', 6))
    hj = join(holes, 'grillecut')
    boolean(tub, hj)
    grille_back = rounded_box('SpeakerFelt', coll, (64, 2, 26), (0, -88.5, 30.5), 1, 2)

    # rear USB-C port + power button
    boolean(tub, rounded_box('usbcut', coll, (10, 30, 4), (40, -95, 40), 1.6, 4))
    btn = prim_cyl('PowerButton', coll, 3.2, 6, (-40, -89.0, 40), 'Y', 32)
    boolean(tub, prim_cyl('btncut', coll, 3.8, 30, (-40, -96, 40), 'Y', 32))

    # front tub: chin light slit (accent) + caster bosses below
    chin = rounded_box('ChinAccent', coll, (70, 6, 3.2), (0, 97.5, 26), 1.5, 4)
    clipc = loft_body('chinclip', coll, Z_BOTTOM, Z_TUB_TOP, inset=-0.6)
    boolean(chin, clipc, op='INTERSECT')

    for ob in (tub, ring, can, visor):
        smooth_by_angle(ob, 50)

    set_mat(tub, M['graphite'])
    set_mat(ring, M['glow'])
    set_mat(can, M['white'])
    set_mat(visor, M['visor'])
    set_mat(tray, M['graphite'])
    set_mat(win, M['led_matrix'])
    set_mat(grille_back, M['grille'])
    set_mat(btn, M['orange'])
    set_mat(chin, M['orange'])
    R.tub, R.ring, R.canopy, R.visor, R.tray, R.matrix = tub, ring, can, visor, tray, win
    R.body_parts = [tub, ring, can, visor, tray, win, grille_back, btn, chin]

    # ---------------- eyes: HC-SR04 transducers + glowing bezels
    eyes = []
    for sx in (-1, 1):
        cx = sx * 13.0
        can_ = prim_cyl('Transducer', coll, 8.0, 12, (cx, 85.5, 66), 'Y', 64)
        set_mat(can_, M['alu'])
        mesh = prim_cyl('TransducerMesh', coll, 6.6, 1.0, (cx, 91.6, 66), 'Y', 64)
        set_mat(mesh, M['grille'])
        bez = prim_torus('EyeBezel', coll, 8.9, 0.75, (cx, 91.0, 66), 'Y', 64, 12)
        set_mat(bez, M['eye_glow'])
        eyes += [can_, mesh, bez]
    # webcam lens
    lens_ring = prim_cyl('LensRing', coll, 4.9, 6, (0, 79.5, 80.5), 'Y', 48)
    set_mat(lens_ring, M['graphite'])
    lens = prim_sphere('Lens', coll, 3.4, (0, 0, 0), 32, 16)
    lens.data.transform(Matrix.Translation((0, 81.6, 80.5)) @ Matrix.Diagonal((1, 0.45, 1, 1)))
    set_mat(lens, M['lens'])
    eyes += [lens_ring, lens]
    R.eye_bezels = [o for o in eyes if o.name.startswith('EyeBezel')]
    R.body_parts += eyes

    # ---------------- ball casters (front / rear)
    for y in (68.0, -70.0):
        house = prim_cyl('CasterHousing', coll, 9.5, 8, (0, y, 9.5), 'Z', 48)
        bevel(house, 2.0, 3, 40)
        set_mat(house, M['graphite'])
        ball = prim_sphere('CasterBall', coll, 6.0, (0, y, 6.0))
        set_mat(ball, M['steel'])
        R.body_parts += [house, ball]


def join(obs, name):
    bm = bmesh.new()
    for o in obs:
        tmp = bmesh.new()
        tmp.from_mesh(o.data)
        tmp.transform(o.matrix_world if o.parent is None else o.matrix_basis)
        me = bpy.data.meshes.new('t')
        tmp.to_mesh(me)
        tmp.free()
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    coll = obs[0].users_collection[0]
    for o in obs:
        bpy.data.objects.remove(o, do_unlink=True)
    return new_mesh_obj(name, coll, bm=bm)


def build_wheel(coll, M, side):
    """side = -1 (left) / +1 (right). Returns pivot empty (spins about local X)."""
    piv = bpy.data.objects.new(f'WheelPivot_{"L" if side < 0 else "R"}', None)
    coll.objects.link(piv)
    piv.empty_display_size = 20
    piv.location = (side * WHEEL_X, AXLE_Y, AXLE_Z)
    parts = []
    # tire: revolve a rounded profile
    verts, faces = [], []
    segs = 96
    prof = []
    hw = WHEEL_W / 2
    ro, ri = WHEEL_R, 29.0
    # profile in (x, r)
    for k in range(13):
        t = math.pi / 2 * k / 12
        prof.append((hw - 4 + 4 * math.sin(t), ro - 4 + 4 * math.cos(t)))
    prof = [(-x, r) for x, r in reversed(prof)] + prof
    prof += [(hw, ri), (-hw, ri)]
    P = len(prof)
    for i in range(segs):
        a = 2 * math.pi * i / segs
        for x, r in prof:
            verts.append(Vector((x, r * math.cos(a), r * math.sin(a))))
    for i in range(segs):
        for j in range(P):
            a0 = i * P + j
            a1 = i * P + (j + 1) % P
            b1 = ((i + 1) % segs) * P + (j + 1) % P
            b0 = ((i + 1) % segs) * P + j
            faces.append((a0, b0, b1, a1))
    tire = new_mesh_obj('Tire', coll, verts, faces)
    smooth_by_angle(tire, 50)
    # chevron tread blocks
    blocks = []
    nb = 28
    for i in range(nb):
        a = 2 * math.pi * i / nb
        for sgn in (-1, 1):
            b = prim_cube('tb', coll, (6.5, 4.2, 2.6), (sgn * 3.8, 0, 0))
            b.rotation_euler = (0, 0, 0)
            mw = (Matrix.Rotation(a, 4, 'X') @ Matrix.Translation((0, 0, ro - 0.6)) @
                  Matrix.Rotation(math.radians(22 * sgn), 4, 'Z'))
            b.data.transform(mw)
            blocks.append(b)
    tb = join(blocks, 'Treads')
    bevel(tb, 0.6, 2, 40)
    tire = join([tire, tb], 'Tire')
    smooth_by_angle(tire, 45)
    set_mat(tire, M['tpu'])
    parts.append(tire)

    # rim: disc with 5 curved spoke windows
    rim = prim_cyl('Rim', coll, 29.5, 14, (0, 0, 0), 'X', 128)
    bevel(rim, 1.2, 3, 40)
    cuts = []
    for i in range(5):
        a = 2 * math.pi * i / 5
        c = rounded_box('rc', coll, (30, 8.5, 17), (0, 0, 0), 3.5, 4)
        c.data.transform(Matrix.Rotation(a, 4, 'X') @ Matrix.Translation((0, 0, 17.5)) @
                         Matrix.Rotation(math.radians(18), 4, 'X'))
        cuts.append(c)
    boolean(rim, join(cuts, 'rimcut'))
    # dish the outer face
    dish = prim_cyl('dish', coll, 25.0, 6, (side * 8.2, 0, 0), 'X', 96)
    boolean(rim, dish)
    smooth_by_angle(rim, 40)
    set_mat(rim, M['white'])
    parts.append(rim)
    hub = prim_cyl('HubCap', coll, 8.5, 4, (side * 5.5, 0, 0), 'X', 64)
    bevel(hub, 1.5, 4, 40)
    set_mat(hub, M['orange'])
    parts.append(hub)
    screw = prim_cyl('HubScrew', coll, 1.8, 1.2, (side * 7.8, 0, 0), 'X', 6)
    set_mat(screw, M['steel'])
    parts.append(screw)
    for p in parts:
        p.parent = piv
    return piv, parts


def build_arm(coll, M, R):
    # ---------------- shoulder pod + neck (fixed to canopy)
    pts = capsule_x_points((0, SHOULDER.y, SHOULDER.z), 16.5, 12.5, 4.0)
    pod = hull_obj('ShoulderPod', coll, pts)
    neck_pts = capsule_x_points((0, SHOULDER.y, SHOULDER.z - 3), 15.0, 10.0, 3.0)
    neck_pts += [Vector((x, y, 84.0)) for x in (-17, 17) for y in (SHOULDER.y - 15, SHOULDER.y + 12)]
    neck = hull_obj('Neck', coll, neck_pts)
    bevel(neck, 2.5, 4, 30)
    pod = join([pod, neck], 'ShoulderPod')
    smooth_by_angle(pod, 40)
    set_mat(pod, M['white'])
    R.body_parts.append(pod)

    # ---------------- rig empties
    sh = bpy.data.objects.new('ArmShoulder', None)
    coll.objects.link(sh)
    sh.location = SHOULDER
    sh.empty_display_size = 15
    el = bpy.data.objects.new('ArmElbow', None)
    coll.objects.link(el)
    el.parent = sh
    el.location = (0, -L1, 0)
    el.empty_display_size = 12

    # ---------------- link 1 (upper arm, yoke around the pod). local frame at shoulder,
    # pointing -Y.
    p = capsule_x_points((0, 0, 0), 22.5, 13.0, 4.0) + capsule_x_points((0, -L1, 0), 13.2, 10.0, 3.0)
    l1 = hull_obj('Link1', coll, p)
    boolean(l1, prim_cyl('podclr', coll, 14.5, 36.4, (0, 0, 0), 'X', 64))
    # weight-saving window in the side plates
    boolean(l1, rounded_box('win', coll, (22, 18, 40), (0, -26, 0), 4, 4))
    smooth_by_angle(l1, 40)
    set_mat(l1, M['white'])
    caps1 = []
    for sx in (-1, 1):
        c = prim_cyl('ShoulderCap', coll, 8.0, 2.4, (sx * 23.2, 0, 0), 'X', 48)
        bevel(c, 0.8, 3, 40)
        set_mat(c, M['orange'])
        caps1.append(c)
    # the elbow servo sits in link1's end: blue servo peeking out
    for o in [l1] + caps1:
        o.parent = sh
        o.matrix_parent_inverse = Matrix.Identity(4)
    # --- shift into shoulder local coords (they were built around origin already)

    # ---------------- link 2 (forearm + claw), local frame at elbow, pointing -Y when straight
    p2 = capsule_x_points((0, 0, 0), 18.0, 11.5, 3.5) + capsule_x_points((0, -L2 + 14, 0), 7.0, 6.5, 2.5)
    l2 = hull_obj('Link2', coll, p2)
    boolean(l2, prim_cyl('hubclr', coll, 12.0, 27.4, (0, 0, 0), 'X', 64))
    boolean(l2, rounded_box('win2', coll, (14, 30, 40), (0, -40, 0), 4, 4))
    smooth_by_angle(l2, 40)
    set_mat(l2, M['white'])
    # claw: two curved fingers forming a fixed hook / scoop at the tip
    fingers = []
    for sx in (-1, 1):
        pts = []
        for k in range(9):
            t = k / 8
            ang = math.radians(-10 + 70 * t)        # curls towards +Z (the "palm" side)
            yy = -L2 + 14 - 22 * math.sin(math.radians(80 * t)) * 1.0
            zz = 2 + 14 * (1 - math.cos(math.radians(80 * t)))
            for dx in (-2.4, 2.4):
                for dz in (-2.6, 2.6):
                    pts.append(Vector((sx * 5.0 + dx, yy, zz + dz)))
        f = hull_obj('Finger', coll, pts)
        bevel(f, 1.0, 3, 30)
        smooth_by_angle(f, 40)
        set_mat(f, M['graphite'])
        fingers.append(f)
    tip = prim_cyl('TipPad', coll, 4.5, 4, (0, -L2 + 11, -5.5), 'Z', 32)
    bevel(tip, 1.0, 3, 40)
    set_mat(tip, M['tpu'])
    tipled = prim_sphere('TipLED', coll, 1.8, (0, -L2 + 9, 4.0), 24, 12)
    set_mat(tipled, M['eye_glow'])
    elbow_core = hull_obj('ElbowHub', coll, capsule_x_points((0, 0, 0), 12.4, 9.8, 3.0))
    smooth_by_angle(elbow_core, 40)
    set_mat(elbow_core, M['servo'])
    caps2 = []
    for sx in (-1, 1):
        c = prim_cyl('ElbowCap', coll, 6.5, 2.2, (sx * 18.6, 0, 0), 'X', 48)
        bevel(c, 0.7, 3, 40)
        set_mat(c, M['orange'])
        caps2.append(c)
    for o in [l2, tip, tipled] + fingers + caps2:
        o.parent = el
    elbow_core.parent = el
    R.shoulder, R.elbow = sh, el
    R.arm_parts = [l1, l2, tip, tipled, elbow_core] + fingers + caps1 + caps2


def build_internals(coll, M, R):
    """Proxy electronics for the exploded / x-ray views."""
    parts = []

    def box(name, size, loc, mat, r=0.6):
        b = rounded_box(name, coll, size, loc, r, 2)
        set_mat(b, M[mat])
        parts.append(b)
        return b
    box('PowerBank', (71, 147, 14.5), (0, -8, 15.5), 'battery', 4)
    box('UnoQ', (53.3, 68.6, 1.6), (0, -20, 30), 'pcb', 0.8)
    box('UnoQ_Chip', (14, 14, 1.5), (0, -16, 31.5), 'grille', 0.3)
    box('UnoQ_Matrix', (30, 18, 0.8), (0, -40, 31.2), 'grille', 0.2)
    box('HC_SR04', (45, 2, 20), (0, 78.5, 66), 'pcb_green', 0.3)
    box('Webcam', (24, 14, 18), (0, 70, 80), 'grille', 2)
    spk = prim_cyl('Speaker', coll, 20, 14, (0, -78, 30), 'Y', 48)
    set_mat(spk, M['grille'])
    parts.append(spk)
    for sx in (-1, 1):
        box('DriveServo', (22.5, 23, 12.5), (sx * 30, 0, AXLE_Z), 'servo', 0.8)
    box('ShoulderServo', (22.5, 12.5, 23), (0, SHOULDER.y, SHOULDER.z - 4), 'servo', 0.8)
    R.internals = parts
    for p in parts:
        p.hide_render = True
        p.hide_viewport = True


def build_robot(name='NOVA', location=(0, 0, 0), scale=0.001):
    """Build the whole robot into a new collection. Returns a Robot handle."""
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    M = make_materials()
    R = Robot()
    R.coll = coll
    R.M = M
    build_body(coll, M, R)
    build_arm(coll, M, R)
    R.wheels = []
    for side in (-1, 1):
        piv, parts = build_wheel(coll, M, side)
        R.wheels.append(piv)
        R.body_parts += parts
    build_internals(coll, M, R)

    root = bpy.data.objects.new(name, None)
    coll.objects.link(root)
    root.empty_display_size = 0.08
    root.scale = (scale, scale, scale)
    root.location = location
    for o in list(coll.objects):
        if o is root or o.parent is not None:
            continue
        o.parent = root
    R.root = root
    pose_arm(R, 0, 180)
    return R


# ================================================================ animation
def pose_arm(R, arm1, arm2, frame=None):
    R.shoulder.rotation_euler = (-math.radians(arm1), 0, 0)
    R.elbow.rotation_euler = (-math.radians(180 - arm2), 0, 0)
    if frame is not None:
        R.shoulder.keyframe_insert('rotation_euler', index=0, frame=frame)
        R.elbow.keyframe_insert('rotation_euler', index=0, frame=frame)


def set_mood(R, rgb, strength=None, frame=None):
    for key in ('glow', 'eye_glow'):
        b = _principled(R.M[key])
        b.inputs['Emission Color'].default_value = (*rgb, 1)
        if strength is not None:
            b.inputs['Emission Strength'].default_value = strength * (1.5 if key == 'eye_glow' else 1.0)
        if frame is not None:
            b.inputs['Emission Color'].keyframe_insert('default_value', frame=frame)
            if strength is not None:
                b.inputs['Emission Strength'].keyframe_insert('default_value', frame=frame)


def set_mood_mat(M, rgb, strength):
    for key in ('glow', 'eye_glow'):
        b = _principled(M[key])
        b.inputs['Emission Color'].default_value = (*rgb, 1)
        b.inputs['Emission Strength'].default_value = strength


def wheel_angle_for_distance(d_m):
    return d_m / (WHEEL_R * 0.001)


def ease_all(obj_or_data, interp='BEZIER'):
    ad = getattr(obj_or_data, 'animation_data', None)
    if not ad or not ad.action:
        return
    for fc in _fcurves(ad.action):
        for k in fc.keyframe_points:
            k.interpolation = interp


def _fcurves(action):
    """Blender 4.4+ layered actions keep fcurves in channelbags."""
    if hasattr(action, 'fcurves') and len(getattr(action, 'fcurves', [])):
        return list(action.fcurves)
    out = []
    for layer in getattr(action, 'layers', []):
        for strip in layer.strips:
            for cb in getattr(strip, 'channelbags', []):
                out += list(cb.fcurves)
    return out
