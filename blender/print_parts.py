"""
NOVA rover - printable parts (hollow shells with real mounting features) + STL export.

  blender -b -P print_parts.py              -> writes ../3d/nova/*.stl and out/print_report.txt
  import print_parts; print_parts.build(coll)  -> dict name -> object (assembly coords, mm)

Everything is in millimetres, assembly coordinates (+Y front, +Z up). The exporter
rotates each part into its print orientation and drops it on z = 0.
"""
import os
import sys
import math
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
import bmesh
from mathutils import Vector, Matrix, Euler
import robot_lib as rl
from robot_lib import (prim_cyl, prim_cube, rounded_box, prim_sphere, boolean, join, loft_body, hull_obj,
                       capsule_x_points, smooth_by_angle, WHEEL_R, AXLE_Y, AXLE_Z, Z_BOTTOM, Z_TUB_TOP,
                       Z_CAN_BOT, Z_TOP, SHOULDER, L1, L2, BAY_FLOOR)

WALL = 2.4            # shell wall
FLOOR = 2.4
RING_WALL = 2.6
BOSSES_FRONT = [(-46.0, 58.0), (46.0, 58.0)]
BOSSES_REAR = [(-32.0, -76.0), (32.0, -76.0)]
SERVO = dict(L=23.0, W=12.5, H=22.5, tab_L=32.4, tab_t=2.5, tab_from_top=4.5, shaft_off=5.6, gear_h=4.0)
CLR = 0.3             # print clearance


def arch_cutter(coll, extra=0.0, x0=43.0):
    cs = [prim_cyl('arch', coll, WHEEL_R + 5.0 + extra, 80, (sx * (x0 - extra + 40), AXLE_Y, AXLE_Z), 'X', 128)
          for sx in (-1, 1)]
    return join(cs, 'archcut')


def union(ob, other):
    boolean(ob, other, op='UNION')


def cut(ob, other):
    boolean(ob, other, op='DIFFERENCE')


def clip(ob, other):
    boolean(ob, other, op='INTERSECT')


def cyl_z(coll, r, z0, z1, x, y, segs=40):
    return prim_cyl('c', coll, r, z1 - z0, (x, y, (z0 + z1) / 2), 'Z', segs)


def box(coll, x0, x1, y0, y1, z0, z1):
    return prim_cube('b', coll, (x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))


# ------------------------------------------------------------------ tub
def build_tub(coll):
    tub = loft_body('P_Tub', coll, Z_BOTTOM, Z_TUB_TOP, segs=192)
    cut(tub, arch_cutter(coll, 0))
    cav = loft_body('cav', coll, Z_BOTTOM + FLOOR, Z_TUB_TOP + 6, inset=WALL, segs=192)
    cut(cav, arch_cutter(coll, WALL))
    cut(tub, cav)

    # battery rails, deck ribs, screw bosses - clipped to the outer skin
    adds = []
    for sx in (-1, 1):
        adds.append(box(coll, sx * 36.6 - 1.2, sx * 36.6 + 1.2, -70, 60, Z_BOTTOM + 1, Z_BOTTOM + FLOOR + 6))
        for y in (-25.0, 25.0):
            x_in, x_out = sorted((sx * 36.4, sx * 42.0))
            adds.append(box(coll, x_in, x_out, y - 5, y + 5, 39.5, 42.5))
    for x, y in BOSSES_FRONT + BOSSES_REAR:
        adds.append(cyl_z(coll, 4.4, Z_BOTTOM + 0.5, Z_TUB_TOP, x, y))
    a = join(adds, 'adds')
    skin = loft_body('skin', coll, Z_BOTTOM, Z_TUB_TOP, segs=192)
    clip(a, skin)
    union(tub, a)

    holes = []
    for x, y in BOSSES_FRONT + BOSSES_REAR:
        holes.append(cyl_z(coll, 1.7, Z_BOTTOM - 2, Z_TUB_TOP + 1, x, y, 24))          # M3 clearance
        holes.append(cyl_z(coll, 3.3, Z_BOTTOM - 2, Z_BOTTOM + 3.0, x, y, 32))         # counterbore
    # drive servo pockets through the arch inner walls (+ 2 screw holes for the tabs)
    for sx in (-1, 1):
        cy = AXLE_Y - SERVO['shaft_off']
        holes.append(prim_cube('sp', coll, (8, SERVO['L'] + 2 * CLR, SERVO['W'] + 2 * CLR), (sx * 42, cy, AXLE_Z)))
        for dy in (-14.0, 14.0):
            holes.append(prim_cyl('sh', coll, 0.9, 10, (sx * 42, cy + dy, AXLE_Z), 'X', 16))
    # caster openings + flange screw holes
    for y in (68.0, -70.0):
        holes.append(cyl_z(coll, 11.2, Z_BOTTOM - 2, Z_BOTTOM + FLOOR + 1, 0, y, 48))
        for dx in (-12.5, 12.5):
            holes.append(cyl_z(coll, 1.1, Z_BOTTOM - 2, Z_BOTTOM + FLOOR + 1, dx, y, 16))
    # rear speaker grille
    for row in range(5):
        for col in range(-6, 7):
            x = col * 4.8 + (2.4 if row % 2 else 0)
            if abs(x) > 28:
                continue
            holes.append(prim_cyl('h', coll, 2.0, 12, (x, -92, 22 + row * 4.2), 'Y', 6))
    holes.append(rounded_box('usb', coll, (10, 14, 4), (40, -92, 40), 1.6, 4))
    holes.append(prim_cyl('btn', coll, 3.8, 14, (-40, -92, 40), 'Y', 32))
    holes.append(box(coll, -35.2, 35.2, 98.5, 112, 24.2, 27.8))                         # chin inlay groove
    cut(tub, join(holes, 'holes'))
    smooth_by_angle(tub, 50)
    return tub


def build_deck(coll):
    """Electronics deck (breadboard + wiring) resting on the 4 ribs above the drive servos."""
    deck = loft_body('P_Deck', coll, 42.6, 45.0, inset=WALL + 0.5, segs=160, steps=3)
    clip(deck, box(coll, -40.3, 40.3, -120, 120, 40, 50))
    holes = [cyl_z(coll, 5.0, 40, 50, x, y) for x, y in BOSSES_REAR]
    holes += [rounded_box('ch', coll, (24, 12, 10), (0, 55, 44), 3, 3),       # cable pass front
              rounded_box('ch', coll, (24, 12, 10), (0, -62, 44), 3, 3),      # cable pass rear (speaker)
              rounded_box('ch', coll, (10, 30, 10), (-33, 0, 44), 3, 3),
              rounded_box('ch', coll, (10, 30, 10), (33, 0, 44), 3, 3)]
    cut(deck, join(holes, 'h'))
    # breadboard fence (half-size breadboard 82.5 x 54.5)
    fence = []
    for x0, x1, y0, y1 in ((-29, 29, 36.5, 38.5), (-29, 29, -48.5, -46.5)):
        fence.append(box(coll, x0, x1, y0, y1, 44.9, 48.0))
    union(deck, join(fence, 'fence'))
    return deck


# ------------------------------------------------------------------ canopy (+ shoulder pod)
def pod_solid(coll):
    pts = capsule_x_points((0, SHOULDER.y, SHOULDER.z), 16.5, 12.5, 4.0)
    pod = hull_obj('pod', coll, pts)
    neck_pts = capsule_x_points((0, SHOULDER.y, SHOULDER.z - 3), 15.0, 10.0, 3.0)
    neck_pts += [Vector((x, y, 84.0)) for x in (-17, 17) for y in (SHOULDER.y - 15, SHOULDER.y + 12)]
    neck = hull_obj('neck', coll, neck_pts)
    rl.bevel(neck, 2.5, 4, 30)
    union(pod, neck)
    return pod


def servo_pocket_vertical(coll, center_x_shaft, axis_pt, open_down_to):
    """SG90 with its shaft along +X at axis_pt, body hanging vertically (length along Z),
    slid in from below. Returns joined cutter."""
    S = SERVO
    cz = axis_pt.z - S['shaft_off']                    # body centre (shaft near the top end)
    ys = S['W'] / 2 + CLR
    xs = S['H'] / 2 + CLR
    top = cz + S['L'] / 2 + CLR
    parts = [box(coll, -xs, xs, axis_pt.y - ys, axis_pt.y + ys, open_down_to, top)]
    # mounting tabs band (near the shaft face)
    tx0 = xs - S['tab_from_top'] - S['tab_t'] - CLR
    tx1 = xs - S['tab_from_top'] + CLR
    parts.append(box(coll, tx0, tx1, axis_pt.y - ys, axis_pt.y + ys, open_down_to, cz + S['tab_L'] / 2 + CLR))
    # gear bump + shaft slot out of the +X face
    parts.append(box(coll, xs - 1, xs + 8, axis_pt.y - 3.9, axis_pt.y + 3.9, open_down_to, axis_pt.z + 3.9))
    parts.append(prim_cyl('shaft', coll, 3.9, 12, (xs + 4, axis_pt.y, axis_pt.z), 'X', 32))
    return join(parts, 'servo_pocket')


def build_canopy(coll):
    can = loft_body('P_Canopy', coll, Z_CAN_BOT, Z_TOP, segs=192)
    cut(can, arch_cutter(coll, 0))
    vcut = rounded_box('visorcut', coll, (82, 80, 30), (0, 100, 71), 9, 6)
    bay = rounded_box('baycut', coll, (54, 150, 30), (0, -15, BAY_FLOOR + 15), 6, 5)
    cav = loft_body('cav', coll, Z_CAN_BOT - 6, Z_TOP - WALL, inset=WALL, segs=192)
    cut(cav, arch_cutter(coll, WALL))
    cut(cav, rounded_box('baykeep', coll, (54 + 2 * WALL, 150 + 2 * WALL, 40), (0, -15, BAY_FLOOR - WALL + 20), 6, 5))
    cut(can, cav)
    union(can, pod_solid(coll))
    cut(can, bay)
    adds = []
    for x, y in BOSSES_FRONT + BOSSES_REAR:
        adds.append(cyl_z(coll, 4.4, Z_TUB_TOP, Z_TOP + 5, x, y))
    # Uno Q standoffs hanging under the bay floor (board top faces the matrix window)
    uno_c = Vector((0, -34.0))
    uno_holes = [(-23.2, -30.3), (23.2, -30.3), (-23.2, 30.3), (23.2, 30.3)]
    for dx, dy in uno_holes:
        adds.append(cyl_z(coll, 3.0, BAY_FLOOR - WALL - 11, BAY_FLOOR - WALL + 0.5, uno_c.x + dx, uno_c.y + dy, 32))
    a = join(adds, 'adds')
    skin = loft_body('skin', coll, Z_TUB_TOP, Z_TOP, segs=192)
    clip(a, skin)
    union(can, a)
    cut(can, vcut)
    holes = []
    for x, y in BOSSES_FRONT + BOSSES_REAR:
        holes.append(cyl_z(coll, 1.25, Z_TUB_TOP - 1, Z_TUB_TOP + 16, x, y, 24))     # M3 self-tap pilot
    for dx, dy in uno_holes:
        holes.append(cyl_z(coll, 1.1, BAY_FLOOR - WALL - 12, BAY_FLOOR - WALL - 2, uno_c.x + dx, uno_c.y + dy, 16))
    holes.append(rounded_box('matrixwin', coll, (32, 20, 20), (0, -30, BAY_FLOOR), 2.5, 4))
    holes.append(servo_pocket_vertical(coll, 0, SHOULDER, 70.0))
    holes.append(prim_cyl('idler', coll, 1.25, 10, (-16.5, SHOULDER.y, SHOULDER.z), 'X', 24))
    holes.append(rounded_box('cable', coll, (10, 8, 30), (0, SHOULDER.y - 12, 84), 2, 3))
    cut(can, join(holes, 'holes'))
    smooth_by_angle(can, 50)
    return can


def build_visor(coll):
    """Smoked / gloss-black visor, glued behind the canopy opening (3 mm lip)."""
    outer = loft_body('P_Visor', coll, Z_CAN_BOT, Z_TOP, inset=WALL, segs=192)
    inner = loft_body('vin', coll, Z_CAN_BOT - 2, Z_TOP + 2, inset=WALL + 1.6, segs=192)
    cut(outer, inner)
    clip(outer, rounded_box('vreg', coll, (88, 80, 36), (0, 100, 71), 11, 6))
    holes = [prim_cyl('eye', coll, 8.35, 40, (sx * 13.0, 95, 66), 'Y', 64) for sx in (-1, 1)]   # HC-SR04 16.5 mm
    holes.append(prim_cyl('cam', coll, 5.0, 40, (0, 85, 80.5), 'Y', 48))
    cut(outer, join(holes, 'h'))
    smooth_by_angle(outer, 50)
    return outer


def build_ring(coll):
    ring = loft_body('P_MoodRing', coll, Z_TUB_TOP, Z_CAN_BOT, inset=1.4, segs=192, steps=4)
    cut(ring, arch_cutter(coll, 0))
    cav = loft_body('rc', coll, Z_TUB_TOP - 2, Z_CAN_BOT + 2, inset=1.4 + RING_WALL, segs=192, steps=4)
    cut(cav, arch_cutter(coll, RING_WALL))
    cut(ring, cav)
    return ring


def build_tray(coll):
    tray = rounded_box('P_BayTray', coll, (53.2, 148, 2.0), (0, -15, BAY_FLOOR + 0.0), 1.0, 3)
    clipper = loft_body('trayclip', coll, Z_CAN_BOT, Z_TOP + 10, inset=0.6)
    clip(tray, clipper)
    cut(tray, rounded_box('win', coll, (34.4, 22.4, 10), (0, -30, BAY_FLOOR), 2.5, 4))
    win = rounded_box('P_MatrixWindow', coll, (34, 22, 1.2), (0, -30, BAY_FLOOR + 0.4), 2.5, 4)
    return tray, win


# ------------------------------------------------------------------ arm
def horn_recess(coll, x_face, direction, center, depth=2.2):
    """Single-arm SG90 horn pocket on a plate face (direction +1: pocket goes +X)."""
    cx = x_face + direction * depth / 2
    pts = []
    for (yy, r) in ((0.0, 3.8), (-15.5, 2.3)):
        for k in range(24):
            a = 2 * math.pi * k / 24
            for xx in (x_face - 0.05 * direction, x_face + direction * depth):
                pts.append(Vector((xx, center.y + yy + r * math.cos(a), center.z + r * math.sin(a))))
    rec = hull_obj('horn', coll, pts)
    shaft = prim_cyl('spline', coll, 2.6, 30, (x_face, center.y, center.z), 'X', 32)
    return join([rec, shaft], 'horn')


def build_link1(coll):
    p = capsule_x_points((0, 0, 0), 22.5, 13.0, 4.0) + capsule_x_points((0, -L1, 0), 13.2, 10.0, 3.0)
    l1 = hull_obj('P_Link1', coll, p)
    cut(l1, prim_cyl('podclr', coll, 14.5, 36.4, (0, 0, 0), 'X', 64))
    cut(l1, rounded_box('win', coll, (22, 18, 40), (0, -26, 0), 4, 4))
    holes = [horn_recess(coll, 18.2, +1, Vector((0, 0, 0))),
             prim_cyl('pivot', coll, 1.65, 10, (-20, 0, 0), 'X', 24)]
    # elbow servo pocket: body along -Y inside the beam, opening downward, shaft out of +X
    S = SERVO
    cy = -L1 + S['shaft_off']
    xs, ys, zs = S['H'] / 2 + CLR, S['L'] / 2 + CLR, S['W'] / 2 + CLR
    holes.append(box(coll, -xs, xs, cy - ys, cy + ys, -20, zs))
    holes.append(box(coll, xs - S['tab_from_top'] - S['tab_t'] - CLR, xs - S['tab_from_top'] + CLR,
                     cy - S['tab_L'] / 2 - CLR, cy + S['tab_L'] / 2 + CLR, -20, zs))
    holes.append(box(coll, xs - 1, 20, -L1 - 3.9, -L1 + 3.9, -20, 3.9))
    holes.append(prim_cyl('idler', coll, 1.25, 8, (-13.2, -L1, 0), 'X', 24))
    cut(l1, join(holes, 'h'))
    smooth_by_angle(l1, 40)
    return l1


def build_link2(coll):
    p2 = capsule_x_points((0, 0, 0), 18.0, 11.5, 3.5) + capsule_x_points((0, -L2 + 14, 0), 7.0, 6.5, 2.5)
    l2 = hull_obj('P_Link2', coll, p2)
    cut(l2, prim_cyl('hubclr', coll, 12.0, 27.4, (0, 0, 0), 'X', 64))
    cut(l2, rounded_box('win2', coll, (14, 30, 40), (0, -40, 0), 4, 4))
    fingers = []
    for sx in (-1, 1):
        pts = []
        for k in range(9):
            t = k / 8
            yy = -L2 + 14 - 22 * math.sin(math.radians(80 * t))
            zz = 2 + 14 * (1 - math.cos(math.radians(80 * t)))
            for dx in (-2.4, 2.4):
                for dz in (-2.6, 2.6):
                    pts.append(Vector((sx * 5.0 + dx, yy, zz + dz)))
        f = hull_obj('Finger', coll, pts)
        rl.bevel(f, 1.0, 3, 30)
        fingers.append(f)
    union(l2, join(fingers, 'fingers'))
    holes = [horn_recess(coll, 13.7, +1, Vector((0, 0, 0))),
             prim_cyl('pivot', coll, 1.65, 10, (-16, 0, 0), 'X', 24),
             cyl_z(coll, 1.0, -10, 10, 0, -L2 + 9, 16)]       # tip LED / magnet hole
    cut(l2, join(holes, 'h'))
    smooth_by_angle(l2, 40)
    return l2


# ------------------------------------------------------------------ wheels & small parts
def build_rim(coll):
    """Rim in wheel-local coords (axis X, inner face at -X)."""
    rim = prim_cyl('P_Rim', coll, 29.5, 14, (0, 0, 0), 'X', 128)
    rl.bevel(rim, 1.2, 3, 40)
    cuts = []
    for i in range(5):
        a = 2 * math.pi * i / 5
        c = rounded_box('rc', coll, (30, 8.5, 17), (0, 0, 0), 3.5, 4)
        c.data.transform(Matrix.Rotation(a, 4, 'X') @ Matrix.Translation((0, 0, 17.5)) @
                         Matrix.Rotation(math.radians(18), 4, 'X'))
        cuts.append(c)
    cuts.append(prim_cyl('dish', coll, 25.0, 6, (8.2, 0, 0), 'X', 96))
    # round SG90 horn (20.5 mm disc, 2 mm) + hub, screw through the centre
    cuts.append(prim_cyl('horn', coll, 10.6, 4.4, (-7.0, 0, 0), 'X', 64))
    cuts.append(prim_cyl('hub', coll, 3.9, 9.0, (-7.0, 0, 0), 'X', 32))
    cuts.append(prim_cyl('screw', coll, 1.25, 30, (0, 0, 0), 'X', 16))
    cut(rim, join(cuts, 'c'))
    smooth_by_angle(rim, 40)
    return rim


def build_caster(coll):
    """Ball caster for a 12 mm steel ball - insert the ball during a print pause at z = 9.8 mm."""
    h = cyl_z(coll, 10.9, 0, 12.0, 0, 0, 64)
    fl = cyl_z(coll, 15.0, 0, 1.6, 0, 0, 64)
    union(h, fl)
    rl.bevel(h, 0.6, 2, 40)
    sock = prim_sphere('sock', coll, 6.25, (0, 0, 5.9), 48, 24)
    lip = cyl_z(coll, 5.6, -1, 3, 0, 0, 48)
    holes = [sock, lip] + [cyl_z(coll, 1.2, -1, 5, dx, 0, 16) for dx in (-12.5, 12.5)]
    cut(h, join(holes, 'h'))
    h.name = 'P_Caster'
    return h


def build_chin(coll):
    chin = box(coll, -35, 35, 98.5, 104, 24.4, 27.6)
    rl.bevel(chin, 1.2, 3, 40)
    clipc = loft_body('chinclip', coll, Z_BOTTOM, Z_TUB_TOP, inset=-0.6)
    clip(chin, clipc)
    chin.name = 'P_ChinInlay'
    return chin


# ------------------------------------------------------------------ assemble all
# name: (builder, copies, print rotation deg, material/filament note)
def build(coll):
    parts = {}
    parts['Tub'] = build_tub(coll)
    parts['Deck'] = build_deck(coll)
    parts['Canopy'] = build_canopy(coll)
    parts['Visor'] = build_visor(coll)
    parts['MoodRing'] = build_ring(coll)
    parts['BayTray'], parts['MatrixWindow'] = build_tray(coll)
    parts['Link1'] = build_link1(coll)
    parts['Link2'] = build_link2(coll)
    parts['Rim'] = build_rim(coll)
    # tire / hubcap / caps re-used from the render model geometry
    R = rl.Robot()
    M = rl.make_materials()
    piv, wparts = rl.build_wheel(coll, M, 1)
    for p in wparts:
        p.parent = None
        if p.name.startswith('Tire'):
            parts['Tire'] = p
        elif p.name.startswith('HubCap'):
            p.data.transform(Matrix.Translation((-5.5, 0, 0)))
            parts['HubCap'] = p
        else:
            bpy.data.objects.remove(p, do_unlink=True)
    bpy.data.objects.remove(piv, do_unlink=True)
    cap = prim_cyl('P_JointCap', coll, 8.0, 2.4, (0, 0, 0), 'Z', 48)
    rl.bevel(cap, 0.8, 3, 40)
    parts['JointCapL'] = cap
    cap2 = prim_cyl('P_JointCapS', coll, 6.5, 2.2, (0, 0, 0), 'Z', 48)
    rl.bevel(cap2, 0.7, 3, 40)
    parts['JointCapS'] = cap2
    parts['Caster'] = build_caster(coll)
    parts['ChinInlay'] = build_chin(coll)
    btn = prim_cyl('P_RearButton', coll, 3.2, 6, (0, 0, 0), 'Z', 32)
    parts['RearButton'] = btn
    return parts


PRINT_INFO = {
    #  part            copies  rot (deg)         filament           notes
    'Tub':          (1, (0, 0, 0),     'PLA graphite',        'open side up, no supports'),
    'Deck':         (1, (0, 0, 0),     'PLA any',             ''),
    'Canopy':       (1, (180, 0, 0),   'PLA pearl white',     'roof down; tree supports for pod/servo pocket'),
    'Visor':        (1, (-55, 0, 0),   'PETG black / smoke',  'supports touching buildplate only'),
    'MoodRing':     (1, (0, 0, 0),     'PETG clear/natural',  'translucent - lit by the RGB LED'),
    'BayTray':      (1, (0, 0, 0),     'PLA graphite',        ''),
    'MatrixWindow': (1, (0, 0, 0),     'PETG smoke / acrylic', '1.2 mm'),
    'Link1':        (1, (0, 90, 0),    'PLA pearl white',     'on its side; supports for the servo pocket'),
    'Link2':        (1, (0, 90, 0),    'PLA pearl white',     'on its side'),
    'Rim':          (2, (0, 90, 0),    'PLA pearl white',     'horn side down'),
    'Tire':         (2, (0, 90, 0),    'TPU 95A black',       ''),
    'HubCap':       (2, (0, 90, 0),    'PLA orange',          ''),
    'JointCapL':    (2, (0, 0, 0),     'PLA orange',          'shoulder caps'),
    'JointCapS':    (2, (0, 0, 0),     'PLA orange',          'elbow caps'),
    'Caster':       (2, (0, 0, 0),     'PLA any',             'pause at z=9.8 mm, drop in a 12 mm steel ball'),
    'ChinInlay':    (1, (90, 0, 0),    'PLA orange',          ''),
    'RearButton':   (1, (0, 0, 0),     'PLA orange',          'cosmetic'),
}


def cleanup(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=0.002)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges[:], dist=0.0005)
    loose = [e for e in bm.edges if not e.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='EDGES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_edges], context='VERTS')
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm.to_mesh(ob.data)
    bm.free()


def mesh_stats(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    nm = sum(1 for e in bm.edges if not e.is_manifold)
    vol = bm.calc_volume(signed=False)
    nf = len(bm.faces)
    bm.free()
    return nm, vol, nf


def write_stl(ob, path, rot):
    me = ob.data.copy()
    me.transform(Euler([math.radians(a) for a in rot]).to_matrix().to_4x4())
    zs = [v.co.z for v in me.vertices]
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    me.transform(Matrix.Translation((-(min(xs) + max(xs)) / 2, -(min(ys) + max(ys)) / 2, -min(zs))))
    me.calc_loop_triangles()
    with open(path, 'wb') as f:
        f.write(b'NOVA rover part - mm'.ljust(80, b' '))
        f.write(struct.pack('<I', len(me.loop_triangles)))
        for t in me.loop_triangles:
            n = t.normal
            f.write(struct.pack('<3f', n.x, n.y, n.z))
            for vi in t.vertices:
                c = me.vertices[vi].co
                f.write(struct.pack('<3f', c.x, c.y, c.z))
            f.write(b'\x00\x00')
    size = (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    bpy.data.meshes.remove(me)
    return size


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    coll = bpy.data.collections.new('PRINT')
    bpy.context.scene.collection.children.link(coll)
    parts = build(coll)
    out_dir = os.path.abspath(os.path.join(HERE, '..', '3d', 'nova'))
    os.makedirs(out_dir, exist_ok=True)
    lines = ['# NOVA rover - print report', '',
             '| Part | Qty | Filament | Bounding box, mm (print orientation) | Volume cm3 | Non-manifold edges | Notes |',
             '|---|---|---|---|---|---|---|']
    total = 0.0
    for name, ob in parts.items():
        qty, rot, fil, note = PRINT_INFO[name]
        cleanup(ob)
        ob.name = 'P_' + name
        nm, vol, nf = mesh_stats(ob)
        size = write_stl(ob, os.path.join(out_dir, f'{name}.stl'), rot)
        total += vol * qty / 1000.0
        lines.append(f'| {name} | {qty} | {fil} | {size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} | '
                     f'{vol / 1000:.1f} | {nm} | {note} |')
        print(f'[stl] {name:13s} {size[0]:6.1f} x {size[1]:6.1f} x {size[2]:6.1f}  vol {vol / 1000:6.1f} cm3  '
              f'non-manifold {nm}', flush=True)
    lines += ['', f'Total solid volume: {total:.0f} cm3 (~{total * 1.24 * 0.55:.0f} g PLA at ~40% effective infill/walls)']
    with open(os.path.join(out_dir, 'print_report.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    if '--save' in sys.argv:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'out', 'print_parts.blend'))


if __name__ == '__main__':
    main()
