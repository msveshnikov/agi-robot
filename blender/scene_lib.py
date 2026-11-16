"""Shared scene helpers: reset, render settings, cameras, lights, environments."""
import bpy
import math
import random
from mathutils import Vector

import robot_lib as rl

LIGHT_SCALE = 0.3   # global calibration for area/point light powers


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    return sc


def set_engine(sc, engine='CYCLES', samples=128, res=(1920, 1080), pct=100):
    try:
        sc.render.engine = engine
    except TypeError:
        sc.render.engine = 'BLENDER_EEVEE'
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = pct
    sc.render.film_transparent = False
    try:
        sc.view_settings.view_transform = 'AgX'
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except TypeError:
        try:
            sc.view_settings.view_transform = 'Filmic'
        except TypeError:
            pass
    if sc.render.engine == 'CYCLES':
        sc.cycles.device = 'CPU'
        sc.cycles.samples = samples
        sc.cycles.use_denoising = True
        sc.cycles.use_adaptive_sampling = True
        sc.cycles.adaptive_threshold = 0.02
        sc.cycles.max_bounces = 8
        sc.cycles.glossy_bounces = 4
        sc.cycles.transmission_bounces = 6
        sc.cycles.caustics_reflective = False
        sc.cycles.caustics_refractive = False
        sc.cycles.blur_glossy = 1.0
        try:
            sc.cycles.denoiser = 'OPENIMAGEDENOISE'
        except TypeError:
            pass
    else:
        ee = sc.eevee
        for attr, val in (('taa_render_samples', samples), ('use_gtao', True),
                          ('use_bloom', True), ('use_ssr', True), ('use_raytracing', True),
                          ('use_shadows', True), ('shadow_ray_count', 2), ('shadow_step_count', 6),
                          ('use_fast_gi', True), ('fast_gi_method', 'GLOBAL_ILLUMINATION'),
                          ('ray_tracing_method', 'SCREEN'), ('volumetric_tile_size', '8'),
                          ('use_volumetric_shadows', True)):
            try:
                setattr(ee, attr, val)
            except (AttributeError, TypeError):
                pass
        try:
            ee.ray_tracing_options.resolution_scale = '2'
            ee.ray_tracing_options.screen_trace_quality = 0.5
        except Exception:
            pass
    sc.render.image_settings.file_format = 'PNG'
    sc.render.use_motion_blur = False


def world_color(sc, color=(0.05, 0.05, 0.06), strength=1.0):
    w = bpy.data.worlds.new('World')
    sc.world = w
    w.use_nodes = True
    bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs[0].default_value = (*color, 1)
    bg.inputs[1].default_value = strength
    return w


def world_sky(sc, sun_elev=12.0, sun_rot=40.0, strength=0.35, altitude=500.0, dust=1.0):
    w = bpy.data.worlds.new('Sky')
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = next(n for n in nt.nodes if n.type == 'BACKGROUND')
    sky = nt.nodes.new('ShaderNodeTexSky')
    for t in ('MULTIPLE_SCATTERING', 'NISHITA', 'SINGLE_SCATTERING'):
        try:
            sky.sky_type = t
            break
        except TypeError:
            continue
    for attr, val in (('sun_elevation', math.radians(sun_elev)), ('sun_rotation', math.radians(sun_rot)),
                      ('altitude', altitude), ('air_density', 1.0), ('dust_density', dust),
                      ('sun_intensity', 1.0)):
        try:
            setattr(sky, attr, val)
        except (AttributeError, TypeError):
            pass
    nt.links.new(sky.outputs[0], bg.inputs[0])
    bg.inputs[1].default_value = strength
    return w


def camera(name, loc, target, lens=50, fstop=None, focus_obj=None, sensor=36):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = sensor
    cd.clip_start = 0.005
    cd.clip_end = 200
    cam = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = loc
    aim(cam, target)
    if fstop:
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = fstop
        if focus_obj is not None:
            cd.dof.focus_object = focus_obj
        else:
            cd.dof.focus_distance = (Vector(loc) - Vector(target)).length
    return cam


def aim(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def target_empty(name, loc):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    e.location = loc
    e.empty_display_size = 0.02
    return e


def track_to(obj, target):
    c = obj.constraints.new('TRACK_TO')
    c.target = target
    c.track_axis = 'TRACK_NEGATIVE_Z'
    c.up_axis = 'UP_Y'
    return c


def area_light(name, loc, target, power, size, color=(1, 1, 1), shape='RECTANGLE', size_y=None):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.energy = power * LIGHT_SCALE
    ld.color = color
    ld.shape = shape
    ld.size = size
    if size_y is not None:
        ld.size_y = size_y
    lo = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.location = loc
    aim(lo, target)
    return lo


def point_light(name, loc, power, color=(1, 1, 1), radius=0.01):
    ld = bpy.data.lights.new(name, 'POINT')
    ld.energy = power * LIGHT_SCALE
    ld.color = color
    ld.shadow_soft_size = radius
    lo = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.location = loc
    return lo


def sun_light(name, rot_deg, power, color=(1, 1, 1), angle=1.0):
    ld = bpy.data.lights.new(name, 'SUN')
    ld.energy = power
    ld.color = color
    ld.angle = math.radians(angle)
    lo = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.rotation_euler = [math.radians(a) for a in rot_deg]
    return lo


def mesh_plane(name, size, loc=(0, 0, 0), mat=None, coll=None):
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=size / 2)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    (coll or bpy.context.scene.collection).objects.link(ob)
    ob.location = loc
    if mat:
        me.materials.append(mat)
    return ob


# ------------------------------------------------------------ materials (env)
def node_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree, rl._principled(m)


def mat_cyclorama(color=(0.8, 0.8, 0.82), rough=0.6):
    m, nt, b = node_mat('Cyclorama')
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    return m


def mat_wood_floor():
    """Procedural oak parquet planks (object coords in metres)."""
    m, nt, b = node_mat('OakFloor')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    nt.links.new(tc.outputs['Object'], mp.inputs[0])
    brick = nt.nodes.new('ShaderNodeTexBrick')
    brick.offset = 0.37
    brick.offset_frequency = 1
    brick.squash = 1.0
    brick.inputs['Scale'].default_value = 1.0
    brick.inputs['Mortar Size'].default_value = 0.0015
    brick.inputs['Brick Width'].default_value = 0.9
    brick.inputs['Row Height'].default_value = 0.12
    brick.inputs['Color1'].default_value = (0.42, 0.24, 0.12, 1)
    brick.inputs['Color2'].default_value = (0.30, 0.16, 0.08, 1)
    brick.inputs['Mortar'].default_value = (0.08, 0.04, 0.02, 1)
    nt.links.new(mp.outputs[0], brick.inputs['Vector'])
    # grain
    mg = nt.nodes.new('ShaderNodeMapping')
    mg.inputs['Scale'].default_value = (2.0, 60.0, 2.0)
    nt.links.new(tc.outputs['Object'], mg.inputs[0])
    noise = nt.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 3.0
    noise.inputs['Detail'].default_value = 8.0
    noise.inputs['Distortion'].default_value = 2.0
    nt.links.new(mg.outputs[0], noise.inputs['Vector'])
    mix = nt.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.blend_type = 'MULTIPLY'
    mix.inputs['Factor'].default_value = 0.55
    nt.links.new(brick.outputs['Color'], mix.inputs[6])
    nt.links.new(noise.outputs['Color'], mix.inputs[7])
    nt.links.new(mix.outputs[2], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.32
    b.inputs['Coat Weight'].default_value = 0.35
    b.inputs['Coat Roughness'].default_value = 0.15
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.15
    nt.links.new(brick.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def mat_sand(color=(0.55, 0.22, 0.09)):
    m, nt, b = node_mat('MarsSand')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    n1 = nt.nodes.new('ShaderNodeTexNoise')
    n1.inputs['Scale'].default_value = 4.0
    n1.inputs['Detail'].default_value = 10
    nt.links.new(tc.outputs['Object'], n1.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (color[0] * 0.6, color[1] * 0.6, color[2] * 0.6, 1)
    ramp.color_ramp.elements[1].color = (min(1, color[0] * 1.25), color[1] * 1.2, color[2] * 1.2, 1)
    nt.links.new(n1.outputs['Fac'], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.92
    n2 = nt.nodes.new('ShaderNodeTexNoise')
    n2.inputs['Scale'].default_value = 400.0
    n2.inputs['Detail'].default_value = 2
    nt.links.new(tc.outputs['Object'], n2.inputs['Vector'])
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.35
    bump.inputs['Distance'].default_value = 0.002
    nt.links.new(n2.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def mat_rock(color=(0.32, 0.14, 0.07)):
    m, nt, b = node_mat('MarsRock')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    vor = nt.nodes.new('ShaderNodeTexVoronoi')
    vor.inputs['Scale'].default_value = 60
    nt.links.new(tc.outputs['Object'], vor.inputs['Vector'])
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = 0.85
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.6
    nt.links.new(vor.outputs['Distance'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def mat_wet_asphalt():
    m, nt, b = node_mat('WetFloor')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    n = nt.nodes.new('ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = 6
    n.inputs['Detail'].default_value = 6
    nt.links.new(tc.outputs['Object'], n.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.45
    ramp.color_ramp.elements[1].position = 0.6
    ramp.color_ramp.elements[0].color = (0.04, 0.04, 0.04, 1)
    ramp.color_ramp.elements[1].color = (0.6, 0.6, 0.6, 1)
    nt.links.new(n.outputs['Fac'], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], b.inputs['Roughness'])
    b.inputs['Base Color'].default_value = (0.012, 0.012, 0.014, 1)
    n2 = nt.nodes.new('ShaderNodeTexNoise')
    n2.inputs['Scale'].default_value = 300
    nt.links.new(tc.outputs['Object'], n2.inputs['Vector'])
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.08
    nt.links.new(n2.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def mat_emit(name, color, strength):
    m, nt, b = node_mat(name)
    b.inputs['Base Color'].default_value = (0, 0, 0, 1)
    b.inputs['Emission Color'].default_value = (*color, 1)
    b.inputs['Emission Strength'].default_value = strength
    return m


def mat_simple(name, color, rough=0.5, metal=0.0, coat=0.0, trans=0.0):
    m, nt, b = node_mat(name)
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Coat Weight'].default_value = coat
    b.inputs['Transmission Weight'].default_value = trans
    return m


# ------------------------------------------------------------ environments
def cyclorama(size=4.0, height=2.0, radius=0.6, mat=None):
    """Seamless studio backdrop: floor curving up into a back wall (+Y)."""
    import bmesh
    verts, faces = [], []
    prof = []
    flat = size / 2
    prof.append((-size / 2, 0))
    steps = 16
    for i in range(steps + 1):
        a = (math.pi / 2) * i / steps
        prof.append((flat - radius + radius * math.sin(a), radius - radius * math.cos(a)))
    prof.append((flat, height))
    nx = 2
    W = size * 1.5
    for x in (-W / 2, W / 2):
        for y, z in prof:
            verts.append((x, y, z))
    P = len(prof)
    for j in range(P - 1):
        faces.append((j, j + 1, P + j + 1, P + j))
    me = bpy.data.meshes.new('Cyclorama')
    me.from_pydata(verts, [], faces)
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new('Cyclorama', me)
    bpy.context.scene.collection.objects.link(ob)
    if mat:
        me.materials.append(mat)
    sub = ob.modifiers.new('sub', 'SUBSURF')
    sub.levels = 2
    sub.render_levels = 2
    return ob


def terrain(name, size, res, height, seed=1, mat=None, flat_center=0.0, freq=0.6):
    """Noise-displaced ground grid (applied), flattened near origin."""
    import bmesh
    from mathutils import noise
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=res, y_segments=res, size=size / 2)
    off = Vector((seed * 13.1, seed * 7.7, 0))
    for v in bm.verts:
        p = v.co
        h = noise.fractal(p * freq + off, 0.5, 2.0, 6) * height
        h += noise.noise(p * freq * 6.0 + off) * height * 0.05
        d = math.hypot(p.x, p.y)
        if flat_center > 0:
            k = min(1.0, max(0.0, (d - flat_center) / (flat_center * 2)))
            h *= k * k
        v.co.z = h
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if mat:
        me.materials.append(mat)
    return ob


def rock(name, loc, size, seed, mat):
    import bmesh
    from mathutils import noise
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=4, radius=1.0)
    off = Vector((seed * 3.3, seed * 1.7, seed * 5.1))
    for v in bm.verts:
        n = v.co.normalized()
        d = 1.0 + 0.35 * noise.fractal(n * 1.5 + off, 0.6, 2.0, 4)
        v.co = n * d
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    rnd = random.Random(seed)
    ob.scale = (size * rnd.uniform(0.8, 1.3), size * rnd.uniform(0.8, 1.3), size * rnd.uniform(0.45, 0.8))
    ob.rotation_euler = (rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), rnd.uniform(0, 6.28))
    me.materials.append(mat)
    return ob


def save_blend(path):
    bpy.ops.wm.save_as_mainfile(filepath=path, compress=True)
