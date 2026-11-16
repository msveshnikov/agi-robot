"""Quick look-dev preview: blender -b -P preview.py -- [arm1 arm2] [view]"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, math
import scene_lib as sl, robot_lib as rl
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
a1 = float(argv[0]) if len(argv) > 0 else 0
a2 = float(argv[1]) if len(argv) > 1 else 180
views = argv[2].split(',') if len(argv) > 2 else ['34']
samples = int(argv[3]) if len(argv) > 3 else 24
t = time.time()
sc = sl.reset()
R = rl.build_robot()
print('build time', time.time() - t)
rl.pose_arm(R, a1, a2)
sl.set_engine(sc, 'CYCLES', samples, (960, 640))
sl.world_color(sc, (0.6, 0.62, 0.66), 0.6)
sl.cyclorama(4, 2, 0.6, sl.mat_cyclorama())
sl.area_light('Key', (0.5, -0.4, 0.6), (0, 0, 0.05), 60, 0.5)
sl.area_light('Rim', (-0.4, 0.5, 0.4), (0, 0, 0.05), 40, 0.4)
dirs = {'34': (0.32, 0.38, 0.22), 'front': (0, 0.55, 0.08), 'side': (0.55, 0, 0.1), 'back': (-0.25, -0.4, 0.25),
        'top': (0.001, 0.05, 0.6), 'low': (0.3, 0.32, 0.04), 'wheel': (0.25, 0.08, 0.05)}
for v in views:
    d = dirs[v]
    cam = sl.camera('Cam_' + v, d, (0, 0.0, 0.055), lens=50)
    sc.camera = cam
    sc.render.filepath = os.path.join(os.path.dirname(__file__), 'out', 'preview', f'p_{v}_{int(a1)}_{int(a2)}.png')
    bpy.ops.render.render(write_still=True)
    print('rendered', v, time.time() - t)
if '--save' in sys.argv:
    sl.save_blend(os.path.join(os.path.dirname(__file__), 'out', 'preview.blend'))
