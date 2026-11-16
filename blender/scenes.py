"""
NOVA rover - scenes, stills and animations.

Usage (from the blender/ folder):
  blender -b -P scenes.py -- <scene> still [samples] [scale%]
  blender -b -P scenes.py -- <scene> video [start end] [scale%]
  blender -b -P scenes.py -- <scene> save          (writes out/<scene>.blend)

Scenes: studio, hero_dark, livingroom, mars, neon, printbed, exploded, macro
"""
import sys
import os
import math
import random
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
from mathutils import Vector, Matrix, Euler
import scene_lib as sl
import robot_lib as rl

OUT = os.path.join(HERE, 'out')
FPS = 24
TRACK = 0.112          # wheel centre distance, m
WHEEL_R = rl.WHEEL_R * 0.001


# ======================================================== compositor bloom
def add_glare(sc, threshold=1.0, strength=0.6, size=7, fog=False):
    threshold = max(threshold, 2.5)
    strength *= 0.35
    try:
        tree = bpy.data.node_groups.new('Comp', 'CompositorNodeTree')
        sc.compositing_node_group = tree
        out = tree.nodes.new('NodeGroupOutput')
        tree.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    except Exception:
        sc.use_nodes = True
        tree = sc.node_tree
        out = next(n for n in tree.nodes if n.type == 'COMPOSITE')
    rlay = tree.nodes.new('CompositorNodeRLayers')
    gl = tree.nodes.new('CompositorNodeGlare')
    for attr, val in (('glare_type', 'BLOOM'), ('quality', 'HIGH')):
        try:
            setattr(gl, attr, val)
        except (AttributeError, TypeError):
            pass
    for key, val in (('Threshold', threshold), ('Strength', strength), ('Size', 0.45)):
        if key in gl.inputs:
            try:
                gl.inputs[key].default_value = val
            except Exception:
                pass
    for attr, val in (('threshold', threshold), ('size', size), ('mix', -0.6)):
        try:
            setattr(gl, attr, val)
        except (AttributeError, TypeError):
            pass
    lens = tree.nodes.new('CompositorNodeLensdist')
    try:
        lens.inputs['Dispersion'].default_value = 0.012
        lens.inputs['Distortion'].default_value = 0.0
    except Exception:
        pass
    tree.links.new(rlay.outputs['Image'], gl.inputs['Image'])
    tree.links.new(gl.outputs['Image'], lens.inputs['Image'])
    tree.links.new(lens.outputs['Image'], out.inputs[0])


# ======================================================== drive kinematics
class Driver:
    """Integrates a differential-drive path and keys root + wheel spin per frame."""

    def __init__(self, R, x=0.0, y=0.0, heading=0.0, frame=1):
        self.R = R
        self.x, self.y, self.h = x, y, heading       # heading: rad, 0 = +Y
        self.wl = self.wr = 0.0
        self.f = frame
        self.key()

    def key(self):
        root = self.R.root
        root.location.x, root.location.y = self.x, self.y
        root.rotation_euler = (0, 0, self.h)
        root.keyframe_insert('location', frame=self.f)
        root.keyframe_insert('rotation_euler', frame=self.f)
        wl, wr = self.R.wheels
        wl.rotation_euler = (-self.wl / WHEEL_R, 0, 0)
        wr.rotation_euler = (-self.wr / WHEEL_R, 0, 0)
        wl.keyframe_insert('rotation_euler', index=0, frame=self.f)
        wr.keyframe_insert('rotation_euler', index=0, frame=self.f)

    def go(self, seconds, v=0.0, w_deg=0.0, ease=True):
        """v: m/s forward, w_deg: deg/s (positive = turn left / CCW)."""
        n = max(1, int(round(seconds * FPS)))
        w = math.radians(w_deg)
        for i in range(1, n + 1):
            t0, t1 = (i - 1) / n, i / n
            if ease:
                s0 = (1 - math.cos(math.pi * t0)) / 2
                s1 = (1 - math.cos(math.pi * t1)) / 2
            else:
                s0, s1 = t0, t1
            ds = (s1 - s0) * seconds   # fraction of total motion this frame (eased)
            d = v * ds
            dh = w * ds
            self.h += dh / 2
            self.x += -math.sin(self.h) * d
            self.y += math.cos(self.h) * d
            self.h += dh / 2
            self.wl += d - dh * TRACK / 2
            self.wr += d + dh * TRACK / 2
            self.f += 1
            self.key()
        return self

    def wait(self, seconds):
        self.f += int(round(seconds * FPS))
        self.key()
        return self


def disable_layer_lines():
    """FDM layer-line bump is sub-pixel at video res and only adds EEVEE noise."""
    for m in bpy.data.materials:
        if m.node_tree:
            for n in m.node_tree.nodes:
                if n.type == 'BUMP' and abs(n.inputs['Distance'].default_value - 0.02) < 1e-6:
                    n.inputs['Strength'].default_value = 0.0


def key_arm(R, frame, a1, a2):
    rl.pose_arm(R, a1, a2, frame)


def linear_fcurves(obj):
    rl.ease_all(obj, 'LINEAR')


def setup_robot(location=(0, 0, 0), heading=0.0, arm=(0, 180), mood=(0.1, 0.85, 1.0), mood_str=12.0):
    R = rl.build_robot(location=location)
    R.root.rotation_euler = (0, 0, heading)
    rl.pose_arm(R, *arm)
    rl.set_mood(R, mood, mood_str)
    return R


def render_still(sc, cams, name, samples):
    os.makedirs(os.path.join(OUT, 'renders'), exist_ok=True)
    for i, cam in enumerate(cams):
        sc.camera = cam
        suffix = '' if len(cams) == 1 else f'_{cam.name.split("_")[-1]}'
        sc.render.filepath = os.path.join(OUT, 'renders', f'{name}{suffix}.png')
        t = time.time()
        bpy.ops.render.render(write_still=True)
        print(f'[still] {sc.render.filepath}  {time.time() - t:.1f}s', flush=True)


# ======================================================== scenes
def scene_studio(mode):
    """White seamless studio, product look. Video: turntable + arm unfold."""
    sc = sl.reset()
    sl.world_color(sc, (0.75, 0.77, 0.8), 0.35)
    sl.cyclorama(5, 2.5, 0.9, sl.mat_cyclorama((0.78, 0.79, 0.81), 0.55))
    sl.area_light('Key', (0.55, -0.35, 0.65), (0, 0, 0.05), 55, 0.7)
    sl.area_light('Fill', (-0.7, -0.2, 0.35), (0, 0, 0.05), 18, 1.0)
    sl.area_light('Rim', (-0.3, 0.7, 0.5), (0, 0, 0.06), 45, 0.4)
    sl.area_light('Top', (0, 0, 1.0), (0, 0, 0), 30, 1.2)
    R = setup_robot(arm=(0, 180))
    tgt = sl.target_empty('Tgt', (0, 0.0, 0.055))
    cams = [sl.camera('Cam_34', (0.42, 0.5, 0.24), tgt.location, lens=60, fstop=8, focus_obj=tgt),
            sl.camera('Cam_front', (0.12, 0.62, 0.1), (0, 0.02, 0.06), lens=70, fstop=8)]
    if mode == 'still':
        return sc, cams, R
    # ---- turntable 10 s with arm unfold
    sc.frame_start, sc.frame_end = 1, 240
    turn = sl.target_empty('Turn', (0, 0, 0))
    R.root.parent = turn
    turn.rotation_euler = (0, 0, 0)
    turn.keyframe_insert('rotation_euler', index=2, frame=1)
    turn.rotation_euler = (0, 0, math.radians(360))
    turn.keyframe_insert('rotation_euler', index=2, frame=241)
    linear_fcurves(turn)
    key_arm(R, 1, 0, 180)
    key_arm(R, 50, 0, 180)
    key_arm(R, 95, 95, 170)
    key_arm(R, 130, 175, 95)
    key_arm(R, 165, 175, 80)
    key_arm(R, 185, 130, 140)
    key_arm(R, 225, 0, 180)
    rl.set_mood(R, (0.1, 0.85, 1.0), 12, frame=1)
    rl.set_mood(R, (0.1, 0.85, 1.0), 12, frame=90)
    rl.set_mood(R, (1.0, 0.35, 0.05), 14, frame=130)
    rl.set_mood(R, (1.0, 0.35, 0.05), 14, frame=180)
    rl.set_mood(R, (0.1, 0.85, 1.0), 12, frame=225)
    tgt.location = (0, 0, 0.1)
    cam = sl.camera('Cam_turn', (0.56, 0.52, 0.2), (0, 0, 0.11), lens=50, fstop=8, focus_obj=tgt)
    return sc, [cam], R


def scene_hero_dark(mode):
    """Dark gradient studio with coloured rim lights - hero shot, arm raised."""
    sc = sl.reset()
    sl.world_color(sc, (0.01, 0.012, 0.016), 1.0)
    sl.cyclorama(5, 2.5, 1.0, sl.mat_cyclorama((0.05, 0.055, 0.065), 0.35))
    sl.area_light('Key', (0.5, 0.25, 0.55), (0, 0, 0.06), 30, 0.35)
    sl.area_light('RimCyan', (-0.45, -0.25, 0.25), (0, 0, 0.06), 40, 0.25, color=(0.3, 0.8, 1.0))
    sl.area_light('RimOrange', (0.45, -0.35, 0.2), (0, 0, 0.06), 35, 0.25, color=(1.0, 0.45, 0.15))
    sl.area_light('Top', (0, 0.05, 0.9), (0, 0, 0), 12, 0.8)
    sl.area_light('Strip', (0, -0.9, 0.5), (0, 0, 0.1), 25, 1.5, size_y=0.05)
    R = setup_robot(arm=(120, 120), mood=(0.1, 0.85, 1.0), mood_str=16)
    tgt = sl.target_empty('Tgt', (0, 0.05, 0.08))
    cam = sl.camera('Cam_hero', (0.36, 0.48, 0.12), tgt.location, lens=55, fstop=5.6, focus_obj=tgt)
    add_glare(sc, 1.0, 0.5)
    return sc, [cam], R


def build_livingroom():
    floor = sl.mesh_plane('Floor', 8, (0, 0, 0), sl.mat_wood_floor())
    # rug
    rug_m, nt, b = sl.node_mat('Rug')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    wave = nt.nodes.new('ShaderNodeTexWave')
    wave.inputs['Scale'].default_value = 6
    wave.inputs['Distortion'].default_value = 2
    nt.links.new(tc.outputs['Object'], wave.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (0.55, 0.52, 0.47, 1)
    ramp.color_ramp.elements[1].color = (0.75, 0.72, 0.66, 1)
    nt.links.new(wave.outputs['Fac'], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.95
    b.inputs['Sheen Weight'].default_value = 1.0
    rug = rl.rounded_box('Rug', bpy.context.scene.collection, (1.6, 1.1, 0.008), (-0.9, 0.7, 0.004), 0.003, 2)
    rug.data.materials.append(rug_m)
    # walls
    wall_m = sl.mat_simple('Wall', (0.78, 0.74, 0.68), 0.85)
    wall = rl.prim_cube('Wall', bpy.context.scene.collection, (8, 0.1, 3), (0, 1.55, 1.5))
    wall.data.materials.append(wall_m)
    base = rl.prim_cube('Baseboard', bpy.context.scene.collection, (8, 0.02, 0.09), (0, 1.495, 0.045))
    base.data.materials.append(sl.mat_simple('Baseboard', (0.9, 0.9, 0.88), 0.3, coat=0.3))
    wall2 = rl.prim_cube('WallL', bpy.context.scene.collection, (0.1, 8, 3), (-1.9, 0, 1.5))
    wall2.data.materials.append(wall_m)
    # sofa (background)
    sofa_m = sl.mat_simple('SofaFabric', (0.12, 0.22, 0.28), 0.9)
    C = bpy.context.scene.collection
    for size, loc in (((1.9, 0.85, 0.42), (-0.6, 1.05, 0.24)), ((1.9, 0.25, 0.75), (-0.6, 1.38, 0.45)),
                      ((0.22, 0.85, 0.6), (-1.55, 1.05, 0.33)), ((0.22, 0.85, 0.6), (0.35, 1.05, 0.33))):
        s = rl.rounded_box('Sofa', C, size, loc, 0.06, 4)
        s.data.materials.append(sofa_m)
    leg_m = sl.mat_simple('Oak', (0.35, 0.2, 0.1), 0.4)
    for x in (-1.5, 0.3):
        for y in (0.7, 1.4):
            l = rl.prim_cyl('SofaLeg', C, 0.02, 0.05, (x, y, 0.025), 'Z', 16)
            l.data.materials.append(leg_m)
    # toys: ball + blocks
    ball_m, nt, b = sl.node_mat('ToyBall')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    wave = nt.nodes.new('ShaderNodeTexWave')
    wave.wave_type = 'RINGS'
    wave.inputs['Scale'].default_value = 0.9
    wave.inputs['Distortion'].default_value = 0
    nt.links.new(tc.outputs['Object'], wave.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.interpolation = 'CONSTANT'
    ramp.color_ramp.elements[0].color = (0.85, 0.08, 0.05, 1)
    ramp.color_ramp.elements[1].position = 0.5
    ramp.color_ramp.elements[1].color = (0.95, 0.75, 0.05, 1)
    nt.links.new(wave.outputs['Fac'], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.25
    b.inputs['Coat Weight'].default_value = 0.5
    ball = rl.prim_sphere('Ball', C, 0.03, (0, 0, 0), 48, 24)
    rl.smooth_by_angle(ball, 80)
    ball.data.materials.append(ball_m)
    cols = [(0.05, 0.3, 0.8), (0.95, 0.65, 0.05), (0.1, 0.6, 0.25), (0.85, 0.1, 0.1)]
    blocks = []
    for i, (loc, rz) in enumerate((((0.38, 0.32, 0.02), 20), ((0.43, 0.36, 0.02), -15),
                                   ((0.40, 0.34, 0.06), 35), ((-0.35, 0.45, 0.02), 60))):
        bl = rl.rounded_box(f'Block{i}', C, (0.04, 0.04, 0.04), (0, 0, 0), 0.003, 3)
        bl.location = loc
        bl.rotation_euler = (0, 0, math.radians(rz))
        bl.data.materials.append(sl.mat_simple(f'BlockM{i}', cols[i], 0.35, coat=0.3))
        blocks.append(bl)
    # plant
    pot = rl.prim_cyl('Pot', C, 0.13, 0.32, (0.75, 1.25, 0.16), 'Z', 48, r2=0.15)
    pot.data.materials.append(sl.mat_simple('Ceramic', (0.85, 0.82, 0.78), 0.25, coat=0.5))
    leaf_m = sl.mat_simple('Leaf', (0.05, 0.25, 0.06), 0.5)
    rnd = random.Random(3)
    for i in range(22):
        lf = rl.prim_sphere('Leaf', C, 0.1, (0, 0, 0), 16, 8)
        lf.scale = (0.25, 1.0, 0.03)
        a = rnd.uniform(0, 6.28)
        lf.location = (0.75 + 0.18 * math.cos(a), 1.25 + 0.18 * math.sin(a), 0.42 + rnd.uniform(0, 0.4))
        lf.rotation_euler = (rnd.uniform(-0.6, 0.6), rnd.uniform(-0.8, 0.8), a + 1.57)
        lf.data.materials.append(leaf_m)
    return ball, blocks


def scene_livingroom(mode):
    sc = sl.reset()
    sl.world_sky(sc, sun_elev=14, sun_rot=-60, strength=0.25)
    sun = sl.sun_light('Sun', (62, 0, -125), 4.5, color=(1.0, 0.82, 0.62), angle=1.5)
    sl.area_light('Window', (1.8, -0.6, 1.2), (0, 0.3, 0.1), 260, 1.2, color=(1.0, 0.92, 0.8))
    sl.area_light('Bounce', (-0.4, -1.2, 0.6), (0, 0, 0.1), 40, 1.5, color=(1.0, 0.95, 0.9))
    ball, blocks = build_livingroom()
    tgt = sl.target_empty('Tgt', (0, 0.05, 0.06))
    if mode == 'still':
        h = math.radians(-107)
        R = setup_robot(location=(0.0, 0.0, 0), heading=h, arm=(176, 95),
                        mood=(1.0, 0.55, 0.1), mood_str=10)
        ball.location = (-math.sin(h) * 0.15, math.cos(h) * 0.15, 0.03)
        cam = sl.camera('Cam_living', (0.36, -0.34, 0.1), (0.05, 0.01, 0.06), lens=45, fstop=4.0)
        cam.data.dof.focus_distance = (Vector((0.36, -0.34, 0.1)) - Vector((0.07, -0.02, 0.06))).length
        return sc, [cam], R
    # ---- video: drive, spot the ball, turn, approach, arm taps the ball which rolls away
    R = setup_robot(location=(0.6, -0.9, 0), arm=(0, 180), mood=(0.1, 0.85, 1.0), mood_str=10)
    ball.location = (-0.15, 0.30, 0.03)
    D = Driver(R, 0.6, -0.9, math.radians(30), 1)
    D.go(2.5, v=0.22, w_deg=0)          # drive diagonally forward-left
    D.go(1.6, v=0.0, w_deg=48)          # look around (turn left)
    D.wait(0.4)
    D.go(1.8, v=0.30, w_deg=-18)        # approach the ball
    stop_f = D.f
    # face toward the ball and stop ~13 cm short
    bx, by = ball.location.x, ball.location.y
    dx, dy = bx - D.x, by - D.y
    target_h = math.atan2(-dx, dy)
    dh = math.degrees((target_h - D.h + math.pi) % (2 * math.pi) - math.pi)
    D.go(0.8, v=0, w_deg=dh / 0.8)
    dist = math.hypot(bx - D.x, by - D.y) - 0.155
    D.go(1.2, v=dist / 1.2)
    D.wait(6.5)
    f0 = D.f - int(6.5 * FPS)
    sc.frame_start, sc.frame_end = 1, D.f
    key_arm(R, 1, 0, 180)
    key_arm(R, f0, 0, 180)
    key_arm(R, f0 + 26, 100, 170)
    key_arm(R, f0 + 48, 178, 125)
    key_arm(R, f0 + 62, 178, 110)      # hover over ball
    key_arm(R, f0 + 70, 180, 96)       # touch
    key_arm(R, f0 + 76, 178, 150)      # flick!
    key_arm(R, f0 + 96, 150, 160)
    key_arm(R, f0 + 112, 120, 150)     # celebrate
    key_arm(R, f0 + 120, 140, 120)
    key_arm(R, f0 + 128, 120, 150)
    key_arm(R, f0 + 136, 140, 120)
    key_arm(R, f0 + 144, 120, 150)
    rl.set_mood(R, (0.1, 0.85, 1.0), 10, frame=1)
    rl.set_mood(R, (0.1, 0.85, 1.0), 10, frame=stop_f)
    rl.set_mood(R, (1.0, 0.55, 0.1), 12, frame=stop_f + 12)
    rl.set_mood(R, (1.0, 0.55, 0.1), 12, frame=f0 + 76)
    rl.set_mood(R, (0.2, 1.0, 0.3), 16, frame=f0 + 84)
    # ball rolls away from the flick
    hdir = Vector((-math.sin(D.h), math.cos(D.h), 0))
    ball.keyframe_insert('location', frame=f0 + 76)
    ball.keyframe_insert('rotation_euler', frame=f0 + 76)
    roll = 0.45
    ball.location = ball.location + hdir * roll
    axis = Vector((hdir.y, -hdir.x, 0))
    ang = roll / 0.03
    ball.rotation_euler = (axis * ang).to_tuple()
    ball.keyframe_insert('location', frame=f0 + 140)
    ball.keyframe_insert('rotation_euler', frame=f0 + 140)
    for fc in rl._fcurves(ball.animation_data.action):
        for k in fc.keyframe_points:
            k.interpolation = 'SINE'
            k.easing = 'EASE_OUT'
    # camera: low dolly following the robot
    cam = sl.camera('Cam_drive', (0.9, -0.2, 0.09), (0, 0, 0), lens=40, fstop=4.0)
    trk = sl.target_empty('CamTgt', (0, 0, 0.06))
    cl = trk.constraints.new('COPY_LOCATION')
    cl.target = R.root
    cl.use_z = False
    trk.location.z = 0.06
    tc = cam.constraints.new('TRACK_TO')
    tc.target = trk
    tc.track_axis = 'TRACK_NEGATIVE_Z'
    tc.up_axis = 'UP_Y'
    cam.data.dof.focus_object = trk
    cam.location = (0.95, -0.55, 0.12)
    cam.keyframe_insert('location', frame=1)
    cam.location = (0.55, 0.0, 0.08)
    cam.keyframe_insert('location', frame=int(stop_f))
    cam.location = (0.32, 0.55, 0.075)
    cam.keyframe_insert('location', frame=D.f)
    return sc, [cam], R


def scene_mars(mode):
    sc = sl.reset()
    w = sl.world_sky(sc, sun_elev=9, sun_rot=200, strength=0.18, dust=6.0)
    nt = w.node_tree
    bg = next(n for n in nt.nodes if n.type == 'BACKGROUND')
    sky = next(n for n in nt.nodes if n.type == 'TEX_SKY')
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.blend_type = 'MULTIPLY'
    mix.inputs['Factor'].default_value = 1.0
    mix.inputs[7].default_value = (1.0, 0.55, 0.32, 1)
    nt.links.new(sky.outputs[0], mix.inputs[6])
    nt.links.new(mix.outputs[2], bg.inputs[0])
    sl.sun_light('Sun', (80, 0, 200), 3.2, color=(1.0, 0.72, 0.5), angle=0.6)
    sand = sl.mat_sand()
    ground = sl.terrain('Ground', 10, 420, 0.06, seed=2, mat=sand, flat_center=0.6 if mode == 'still' else 2.2)
    far = sl.terrain('Far', 260, 220, 9, seed=5, mat=sand, flat_center=14, freq=0.025)
    far.location.z = -0.4
    rockm = sl.mat_rock()
    rnd = random.Random(7)
    for i in range(70):
        a = rnd.uniform(0, 6.28)
        d = rnd.uniform(0.35, 3.8)
        s = rnd.uniform(0.01, 0.07) if d < 1.5 else rnd.uniform(0.03, 0.18)
        sl.rock(f'Rock{i}', (math.cos(a) * d, math.sin(a) * d, 0.0), s, i, rockm)
    sl.rock('BigRock', (-0.35, 0.55, 0.02), 0.13, 99, rockm)
    tgt = sl.target_empty('Tgt', (0, 0.0, 0.06))
    if mode == 'still':
        R = setup_robot(location=(0, 0, 0.004), heading=math.radians(25), arm=(150, 110),
                        mood=(0.1, 0.85, 1.0), mood_str=14)
        cam = sl.camera('Cam_mars', (0.34, 0.36, 0.05), (0.0, 0.02, 0.07), lens=32, fstop=5.6)
        return sc, [cam], R
    sc.frame_start, sc.frame_end = 1, 240
    R = setup_robot(location=(0.5, -1.4, 0.004), arm=(0, 180), mood=(0.1, 0.85, 1.0), mood_str=14)
    D = Driver(R, 0.5, -1.4, math.radians(15), 1)
    D.go(3.0, v=0.25, w_deg=8, ease=False)
    D.go(2.0, v=0.25, w_deg=-14, ease=False)
    D.go(1.2, v=0.12, w_deg=0)
    D.go(1.0, v=0, w_deg=35)
    D.wait(3)
    sf = D.f - 3 * FPS
    key_arm(R, 1, 0, 180)
    key_arm(R, sf, 0, 180)
    key_arm(R, sf + 36, 120, 150)      # raise arm like a periscope / point at horizon
    key_arm(R, sf + 60, 140, 175)
    # tracking camera
    cam = sl.camera('Cam_mars', (0, 0, 0), (0, 0, 0), lens=28, fstop=8)
    rig = sl.target_empty('CamRig', (0, 0, 0))
    cl = rig.constraints.new('COPY_LOCATION')
    cl.target = R.root
    cam.parent = rig
    cam.location = (0.38, 0.42, 0.06)
    cam.keyframe_insert('location', frame=1)
    cam.location = (-0.22, 0.45, 0.05)
    cam.keyframe_insert('location', frame=150)
    cam.location = (-0.42, 0.12, 0.09)
    cam.keyframe_insert('location', frame=240)
    trk = sl.target_empty('CamTgt', (0, 0, 0.06))
    trk.parent = rig
    tc = cam.constraints.new('TRACK_TO')
    tc.target = trk
    tc.track_axis = 'TRACK_NEGATIVE_Z'
    tc.up_axis = 'UP_Y'
    cam.data.dof.focus_object = trk
    return sc, [cam], R


def scene_neon(mode):
    sc = sl.reset()
    sl.world_color(sc, (0.004, 0.003, 0.008), 1.0)
    C = sc.collection
    floor = sl.mesh_plane('Floor', 10, (0, 0, 0), sl.mat_wet_asphalt())
    wall_m = sl.mat_simple('Concrete', (0.03, 0.03, 0.035), 0.7)
    wall = rl.prim_cube('Wall', C, (6, 0.1, 3), (0, 0.9, 1.5))
    wall.data.materials.append(wall_m)
    pink = sl.mat_emit('NeonPink', (1.0, 0.05, 0.45), 30)
    cyan = sl.mat_emit('NeonCyan', (0.05, 0.7, 1.0), 30)
    for i, (x, z, ln, m, ax) in enumerate(((-0.55, 0.35, 0.8, pink, 'Z'), (0.6, 0.25, 0.5, cyan, 'Z'),
                                           (0.0, 0.9, 1.6, cyan, 'X'), (-0.2, 0.12, 0.45, pink, 'X'))):
        tube = rl.prim_cyl(f'Neon{i}', C, 0.008, ln, (x, 0.84, z), ax, 16)
        tube.data.materials.append(m)
    sl.area_light('PinkFill', (-0.6, 0.6, 0.35), (0, 0, 0.05), 25, 0.6, color=(1.0, 0.1, 0.5))
    sl.area_light('CyanFill', (0.6, 0.5, 0.3), (0, 0, 0.05), 25, 0.6, color=(0.1, 0.7, 1.0))
    sl.area_light('Front', (0.1, -0.7, 0.25), (0, 0, 0.06), 6, 0.6, color=(0.7, 0.75, 1.0))
    sl.area_light('Top', (0, 0, 0.9), (0, 0, 0), 6, 0.6, color=(0.8, 0.7, 1.0))
    if mode == 'still':
        R = setup_robot(location=(0, 0.0, 0), heading=math.radians(200), arm=(110, 140),
                        mood=(1.0, 0.1, 0.6), mood_str=18)
        cam = sl.camera('Cam_neon', (0.36, -0.58, 0.09), (0.0, 0.0, 0.1), lens=40, fstop=4.0)
        add_glare(sc, 0.9, 0.7)
        return sc, [cam], R
    # ---- wake-up sequence 8 s
    sc.frame_start, sc.frame_end = 1, 192
    R = setup_robot(location=(0, 0.0, 0), heading=math.radians(180), arm=(0, 180),
                    mood=(0.1, 0.85, 1.0), mood_str=0.0)
    mt = R.M['led_matrix'].node_tree
    st = mt.nodes['MatrixStrength']
    st.inputs[1].default_value = 0.0
    st.inputs[1].keyframe_insert('default_value', frame=1)
    st.inputs[1].default_value = 0.0
    st.inputs[1].keyframe_insert('default_value', frame=20)
    st.inputs[1].default_value = 30.0
    st.inputs[1].keyframe_insert('default_value', frame=30)
    wn = mt.nodes['MatrixNoise']
    wn.inputs['W'].default_value = 0
    wn.inputs['W'].keyframe_insert('default_value', frame=1)
    wn.inputs['W'].default_value = 40
    wn.inputs['W'].keyframe_insert('default_value', frame=192)
    for fc in rl._fcurves(mt.animation_data.action):
        if 'MatrixNoise' in fc.data_path:
            for k in fc.keyframe_points:
                k.interpolation = 'CONSTANT'
    # eyes flicker on, ring fades up cyan -> magenta
    seq = [(1, 0), (26, 0), (28, 18), (30, 0), (33, 0), (35, 22), (37, 4), (40, 20), (70, 14)]
    for f, s in seq:
        rl.set_mood(R, (0.1, 0.85, 1.0), s, frame=f)
    rl.set_mood(R, (0.1, 0.85, 1.0), 14, frame=120)
    rl.set_mood(R, (1.0, 0.1, 0.6), 18, frame=140)
    rl.set_mood(R, (1.0, 0.1, 0.6), 18, frame=192)
    key_arm(R, 1, 0, 180)
    key_arm(R, 60, 0, 180)
    key_arm(R, 95, 90, 175)
    key_arm(R, 115, 110, 120)
    key_arm(R, 130, 100, 150)    # wave
    key_arm(R, 145, 110, 120)
    key_arm(R, 160, 100, 150)
    key_arm(R, 192, 110, 140)
    D = Driver(R, 0, 0, math.radians(180), 1)
    D.wait(1.0)
    D.f = 140
    D.key()
    D.go(1.5, v=0.0, w_deg=-12)
    cam = sl.camera('Cam_neon', (0.42, -0.55, 0.05), (0, 0, 0.07), lens=40, fstop=4.0)
    tgt = sl.target_empty('Tgt', (0, 0, 0.1))
    cam.data.dof.focus_object = tgt
    track = cam.constraints.new('TRACK_TO')
    track.target = tgt
    track.track_axis = 'TRACK_NEGATIVE_Z'
    track.up_axis = 'UP_Y'
    cam.keyframe_insert('location', frame=1)
    cam.location = (0.3, -0.5, 0.1)
    cam.keyframe_insert('location', frame=192)
    add_glare(sc, 0.9, 0.7)
    return sc, [cam], R


def printable_parts(R):
    """Map of printable part objects (built geometry) -> material colour label."""
    names = ['Tub', 'Canopy', 'MoodRing', 'Visor', 'BayTray', 'ShoulderPod', 'Link1', 'Link2', 'Finger',
             'Rim', 'Tire', 'HubCap', 'ShoulderCap', 'ElbowCap', 'CasterHousing', 'ChinAccent', 'PowerButton']
    out = []
    for o in R.coll.objects:
        if o.type != 'MESH':
            continue
        base = o.name.split('.')[0]
        if base in names:
            out.append(o)
    return out


PRINT_ROT = {   # orientation for flat lay / printing (deg, applied in robot coords)
    'Tub': (0, 0, 90), 'Canopy': (0, 0, 90), 'MoodRing': (0, 0, 90), 'Visor': (-55, 0, 0),
    'BayTray': (0, 0, 90), 'ShoulderPod': (0, 0, 0), 'Link1': (0, 0, 90), 'Link2': (0, 0, 90),
    'Finger': (0, 90, 0), 'Rim': (0, 90, 0), 'Tire': (0, 90, 0), 'HubCap': (0, 90, 0),
    'ShoulderCap': (0, 90, 0), 'ElbowCap': (0, 90, 0), 'CasterHousing': (0, 0, 0),
    'ChinAccent': (90, 0, 0), 'PowerButton': (90, 0, 0),
}


def world_matrix(o):
    m = o.matrix_basis.copy()
    p = o.parent
    while p is not None:
        m = p.matrix_basis @ m
        p = p.parent
    return m


def bake_world(o):
    mw = world_matrix(o)
    o.parent = None
    o.data = o.data.copy()
    o.data.transform(mw)
    o.matrix_world = Matrix.Identity(4)


PRINT_MAT = {'Tub': 'graphite', 'Deck': 'graphite', 'Canopy': 'white', 'Visor': 'visor', 'MoodRing': 'glow',
             'BayTray': 'graphite', 'MatrixWindow': 'visor', 'Link1': 'white', 'Link2': 'white', 'Rim': 'white',
             'Tire': 'tpu', 'HubCap': 'orange', 'JointCapL': 'orange', 'JointCapS': 'orange', 'Caster': 'graphite',
             'ChinInlay': 'orange', 'RearButton': 'orange'}


def scene_printbed(mode):
    """Knolling: every printed part (real hollow print geometry) laid out on a cutting mat."""
    sc = sl.reset()
    sl.world_color(sc, (0.5, 0.5, 0.52), 0.35)
    C = sc.collection
    M = rl.make_materials()
    rl.set_mood_mat(M, (0.1, 0.85, 1.0), 2.0)
    mat, nt, b = sl.node_mat('CuttingMat')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.offset = 0
    br.inputs['Scale'].default_value = 1.0
    br.inputs['Mortar Size'].default_value = 0.0006
    br.inputs['Brick Width'].default_value = 0.01
    br.inputs['Row Height'].default_value = 0.01
    br.inputs['Color1'].default_value = (0.03, 0.16, 0.1, 1)
    br.inputs['Color2'].default_value = (0.03, 0.16, 0.1, 1)
    br.inputs['Mortar'].default_value = (0.35, 0.55, 0.45, 1)
    nt.links.new(tc.outputs['Object'], br.inputs['Vector'])
    nt.links.new(br.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.7
    desk = rl.prim_cube('Desk', C, (3, 2, 0.03), (0, 0, -0.017))
    desk.data.materials.append(sl.mat_simple('DeskOak', (0.45, 0.3, 0.17), 0.45, coat=0.2))
    # load the print geometry
    import print_parts as pp
    path = os.path.join(OUT, 'print_parts.blend')
    with bpy.data.libraries.load(path) as (src, dst):
        dst.objects = [n for n in src.objects if n.startswith('P_')]
    parts = []
    for o in dst.objects:
        if o is None:
            continue
        name = o.name[2:].split('.')[0]
        if name not in pp.PRINT_INFO:
            continue
        qty, rot, fil, note = pp.PRINT_INFO[name]
        src_me = o.data
        for i in range(qty):
            ob = o if i == 0 else o.copy()
            C.objects.link(ob)
            ob.data = src_me.copy()
            me = ob.data
            me.materials.clear()
            me.materials.append(M[PRINT_MAT[name]])
            me.transform(Euler([math.radians(a) for a in rot]).to_matrix().to_4x4())
            me.transform(Matrix.Diagonal((0.001, 0.001, 0.001, 1)))
            vs = [v.co for v in me.vertices]
            lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
            hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
            me.transform(Matrix.Translation(-lo))
            ob.matrix_world = Matrix.Identity(4)
            rl.smooth_by_angle(ob, 40)
            parts.append((ob, hi - lo))
    parts.sort(key=lambda p: -(p[1].x * p[1].y))
    W, gap = 0.56, 0.018
    x = y = 0.0
    row_h = 0.0
    placed = []
    for o, size in parts:
        if x + size.x > W:
            x = 0.0
            y += row_h + gap
            row_h = 0.0
        placed.append((o, x, y, size))
        x += size.x + gap
        row_h = max(row_h, size.y)
    total_h = y + row_h
    for o, px, py, size in placed:
        o.location = (px - W / 2, -(py - total_h / 2) - size.y, 0.0)
    mw, mh = W + 0.08, total_h + 0.08
    matobj = rl.rounded_box('CuttingMat', C, (mw, mh, 0.002), (0, 0, -0.001), 0.01, 3)
    matobj.data.materials.append(mat)
    sl.area_light('Key', (0.35, -0.45, 0.9), (0, 0, 0), 140, 0.9)
    sl.area_light('Fill', (-0.7, 0.2, 0.6), (0, 0, 0), 50, 1.2)
    sl.area_light('Rim', (0.0, 0.8, 0.5), (0, 0, 0), 60, 0.8, color=(0.9, 0.95, 1.0))
    top_h = max(mw * 1.08 / 0.9, mh * 1.08 / 0.506)
    cams = [sl.camera('Cam_top', (0.0, -0.01, top_h), (0.0, 0.0, 0), lens=40, fstop=16),
            sl.camera('Cam_low', (0.36, -0.42, 0.22), (0.03, -0.02, 0.01), lens=40, fstop=5.6)]
    return sc, cams, None


def explode_offsets():
    """Per-part (dx, dy, dz) in mm for the exploded view (robot local coords)."""
    return {
        'Canopy': (0, 0, 55), 'Visor': (0, 40, 55), 'BayTray': (0, 0, 80), 'MatrixWindow': (0, 0, 86),
        'ShoulderPod': (0, 0, 95), 'ArmShoulder': (0, 0, 108), 'MoodRing': (0, 0, 24),
        'Transducer': (0, 30, 30), 'TransducerMesh': (0, 30, 30), 'EyeBezel': (0, 70, 55),
        'LensRing': (0, 70, 55), 'Lens': (0, 70, 55), 'HC_SR04': (0, 30, 30), 'Webcam': (0, 20, 40),
        'WheelPivot_L': (-75, 0, 0), 'WheelPivot_R': (75, 0, 0), 'DriveServo': (0, 0, 10),
        'Tub': (0, 0, -40), 'CasterHousing': (0, 0, -70), 'CasterBall': (0, 0, -85),
        'PowerBank': (0, 0, -15), 'UnoQ': (0, 0, 25), 'UnoQ_Chip': (0, 0, 25), 'UnoQ_Matrix': (0, 0, 25),
        'Speaker': (0, -40, 15), 'ShoulderServo': (0, 0, 100), 'ChinAccent': (0, 25, -40),
        'SpeakerFelt': (0, -30, -40), 'PowerButton': (0, -25, -40),
    }


def scene_exploded(mode):
    sc = sl.reset()
    w = sl.world_color(sc, (0.02, 0.035, 0.07), 1.0)
    grid_m, nt, b = sl.node_mat('Blueprint')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.inputs['Scale'].default_value = 20
    br.inputs['Mortar Size'].default_value = 0.012
    br.inputs['Brick Width'].default_value = 1.0
    br.inputs['Row Height'].default_value = 1.0
    br.offset = 0
    br.inputs['Color1'].default_value = (0.015, 0.04, 0.09, 1)
    br.inputs['Color2'].default_value = (0.015, 0.04, 0.09, 1)
    br.inputs['Mortar'].default_value = (0.12, 0.3, 0.6, 1)
    nt.links.new(tc.outputs['Object'], br.inputs['Vector'])
    nt.links.new(br.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.6
    sl.cyclorama(6, 3, 1.0, grid_m)
    sl.area_light('Key', (0.6, 0.6, 0.9), (0, 0, 0.1), 90, 0.8)
    sl.area_light('Fill', (-0.7, 0.2, 0.4), (0, 0, 0.1), 40, 1.0, color=(0.6, 0.8, 1.0))
    sl.area_light('Rim', (0, -0.8, 0.6), (0, 0, 0.1), 50, 0.6, color=(0.5, 0.8, 1.0))
    R = setup_robot(arm=(0, 180), mood=(0.1, 0.85, 1.0), mood_str=12)
    for o in R.internals:
        o.hide_render = False
        o.hide_viewport = False
    offs = explode_offsets()
    movers = []
    for o in R.coll.objects:
        base = o.name.split('.')[0]
        if base in offs and (o.parent is R.root):
            movers.append((o, Vector(offs[base])))
    tgt = sl.target_empty('Tgt', (0, 0.0, 0.1))
    if mode == 'still':
        for o, d in movers:
            o.location = o.location + d
        rl.pose_arm(R, 0, 180)
        R.root.location.z = 0.06
        rl.set_mood(R, (0.1, 0.85, 1.0), 5)
        cam = sl.camera('Cam_explode', (0.62, 0.6, 0.34), (0.04, -0.03, 0.13), lens=42, fstop=11)
        add_glare(sc, 1.0, 0.4)
        return sc, [cam], R
    sc.frame_start, sc.frame_end = 1, 192
    R.root.location.z = 0.0
    R.root.keyframe_insert('location', index=2, frame=1)
    R.root.keyframe_insert('location', index=2, frame=30)
    R.root.location.z = 0.06
    R.root.keyframe_insert('location', index=2, frame=70)
    R.root.keyframe_insert('location', index=2, frame=140)
    R.root.location.z = 0.0
    R.root.keyframe_insert('location', index=2, frame=180)
    for o, d in movers:
        base = o.location.copy()
        o.keyframe_insert('location', frame=30)
        o.location = base + d
        o.keyframe_insert('location', frame=80)
        o.keyframe_insert('location', frame=130)
        o.location = base
        o.keyframe_insert('location', frame=175)
    key_arm(R, 30, 0, 180)
    key_arm(R, 80, 0, 180)
    key_arm(R, 130, 0, 180)
    key_arm(R, 175, 0, 180)
    turn = sl.target_empty('Turn', (0, 0, 0))
    R.root.parent = turn
    turn.keyframe_insert('rotation_euler', index=2, frame=1)
    turn.rotation_euler.z = math.radians(120)
    turn.keyframe_insert('rotation_euler', index=2, frame=192)
    linear_fcurves(turn)
    rl.set_mood(R, (0.1, 0.85, 1.0), 5)
    cam = sl.camera('Cam_explode', (0.46, 0.44, 0.27), (0, 0.0, 0.12), lens=40, fstop=11)
    add_glare(sc, 1.0, 0.4)
    return sc, [cam], R


def scene_macro(mode):
    """Close-up of the face on a desk with bokeh lights."""
    sc = sl.reset()
    sl.world_color(sc, (0.02, 0.018, 0.02), 1.0)
    C = sc.collection
    desk = rl.prim_cube('Desk', C, (3, 2, 0.04), (0, 0.3, -0.02))
    desk.data.materials.append(sl.mat_simple('DeskWalnut', (0.12, 0.06, 0.03), 0.35, coat=0.4))
    rnd = random.Random(11)
    for i in range(40):
        col = rnd.choice([(1.0, 0.6, 0.25), (1.0, 0.75, 0.4), (0.3, 0.6, 1.0)])
        p = rl.prim_sphere(f'Bokeh{i}', C, 0.012, (rnd.uniform(-1.4, 1.4), rnd.uniform(1.2, 2.4), rnd.uniform(0.1, 0.9)), 12, 6)
        p.data.materials.append(sl.mat_emit(f'BK{i}', col, rnd.uniform(15, 40)))
    sl.area_light('Key', (0.35, 0.45, 0.35), (0, 0.08, 0.07), 14, 0.3, color=(1.0, 0.9, 0.8))
    sl.area_light('Rim', (-0.4, -0.1, 0.25), (0, 0, 0.07), 20, 0.3, color=(0.5, 0.75, 1.0))
    R = setup_robot(location=(0, 0, 0), heading=math.radians(0), arm=(0, 180),
                    mood=(0.1, 0.85, 1.0), mood_str=16)
    rl.set_mood(R, (0.1, 0.85, 1.0), 4)
    cam = sl.camera('Cam_macro', (0.13, 0.36, 0.085), (0.0, 0.07, 0.065), lens=85, fstop=2.8)
    cam.data.dof.focus_distance = (Vector((0.13, 0.36, 0.085)) - Vector((0.0, 0.09, 0.066))).length
    add_glare(sc, 2.0, 0.35)
    return sc, [cam], R


SCENES = {
    'studio': scene_studio, 'hero_dark': scene_hero_dark, 'livingroom': scene_livingroom,
    'mars': scene_mars, 'neon': scene_neon, 'printbed': scene_printbed,
    'exploded': scene_exploded, 'macro': scene_macro,
}


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    name = argv[0] if argv else 'studio'
    mode = argv[1] if len(argv) > 1 else 'still'
    t = time.time()
    sc, cams, R = SCENES[name]('video' if mode in ('video', 'save', 'test') else 'still')
    print(f'[build] {name} {time.time() - t:.1f}s', flush=True)
    if mode == 'still':
        samples = int(argv[2]) if len(argv) > 2 else 96
        pct = int(argv[3]) if len(argv) > 3 else 100
        sl.set_engine(sc, 'CYCLES', samples, (1920, 1080), pct)
        render_still(sc, cams, name, samples)
    elif mode == 'video':
        f0 = int(argv[2]) if len(argv) > 2 else sc.frame_start
        f1 = int(argv[3]) if len(argv) > 3 else sc.frame_end
        pct = int(argv[4]) if len(argv) > 4 else 100
        eng = argv[5] if len(argv) > 5 else 'BLENDER_EEVEE'
        sl.set_engine(sc, eng, int(os.environ.get('EEVEE_SAMPLES', 8)) if eng != 'CYCLES' else 24, (1280, 720), pct)
        sc.render.fps = FPS
        disable_layer_lines()
        sc.camera = cams[0]
        d = os.path.join(OUT, 'frames', name)
        os.makedirs(d, exist_ok=True)
        sc.render.filepath = os.path.join(d, 'f_')
        sc.render.image_settings.file_format = 'PNG'
        sc.render.use_overwrite = False
        sc.render.use_placeholder = True
        sc.frame_start, sc.frame_end = f0, f1
        bpy.ops.render.render(animation=True)
        print(f'[video] {name} frames {f0}-{f1} done {time.time() - t:.1f}s', flush=True)
    elif mode == 'test':
        frames = [int(f) for f in argv[2].split(',')]
        pct = int(argv[3]) if len(argv) > 3 else 50
        sl.set_engine(sc, 'BLENDER_EEVEE', 4, (1280, 720), pct)
        sc.camera = cams[0]
        for f in frames:
            sc.frame_set(f)
            sc.render.filepath = os.path.join(OUT, 'draft', f'{name}_f{f:04d}.png')
            bpy.ops.render.render(write_still=True)
    elif mode == 'mood':
        # mood-ring variants of a still scene for the web site (EEVEE, fast)
        moods = {'curious': (0.1, 0.85, 1.0), 'happy': (0.15, 1.0, 0.3), 'cautious': (1.0, 0.45, 0.05),
                 'excited': (1.0, 0.1, 0.6), 'thinking': (0.25, 0.3, 1.0), 'blocked': (1.0, 0.05, 0.03)}
        sl.set_engine(sc, 'BLENDER_EEVEE', 24, (1600, 900), 100)
        disable_layer_lines()
        sc.camera = cams[0]
        os.makedirs(os.path.join(OUT, 'moods'), exist_ok=True)
        for k, c in moods.items():
            rl.set_mood(R, c, 16)
            sc.render.filepath = os.path.join(OUT, 'moods', f'{name}_{k}.png')
            bpy.ops.render.render(write_still=True)
    elif mode == 'save':
        sc.camera = cams[0]
        sl.set_engine(sc, 'BLENDER_EEVEE', 32, (1920, 1080))
        os.makedirs(OUT, exist_ok=True)
        sl.save_blend(os.path.join(OUT, f'{name}.blend'))


if __name__ == '__main__':
    main()
