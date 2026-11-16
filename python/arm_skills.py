"""
Arm skills for the NOVA shell (2-DOF arm on the roof, SG90 shoulder + SG90 elbow).

Joint convention (identical to blender/robot_lib.py and sketch/sketch.ino):
    arm1 (shoulder): 0 = folded back into the roof bay, 90 = straight up, 180 = forward
    arm2 (elbow):    180 = straight, 90 = right angle; minimum 20 (mechanical stop)

Geometry (mm, robot frame: y forward from the body centre, z up from the floor):
    shoulder axis at (y=58, z=102), upper arm L1 = 55, forearm L2 = 88 (+ ~20 mm claw)
    front bumper at y = 100, camera lens at (y=82, z=80) looking forward.

The LLM picks a named skill (`arm_action`) instead of raw angles; raw angles are still
accepted for fine control. Every motion goes through the firmware's eased `armPose`.
"""
import math
import time
import logging

logger = logging.getLogger("robot.arm")

SHOULDER = (58.0, 102.0)
L1, L2 = 55.0, 88.0
ARM1_RANGE = (0, 180)
ARM2_RANGE = (20, 180)
PARK = (0, 180)

# Each skill is a list of (arm1, arm2, duration_ms) keyframes.
SKILLS = {
    "park":         [(0, 180, 900)],
    "raise":        [(90, 180, 900)],                                   # periscope - straight up
    "look_around":  [(90, 180, 700), (100, 150, 500), (80, 160, 500), (0, 180, 900)],
    "point_forward": [(150, 165, 800)],
    "hover":        [(178, 120, 1000)],                                 # claw above the floor in front
    "reach_floor":  [(178, 120, 900), (180, 95, 600)],                  # claw on the floor ~13 cm ahead
    "tap":          [(178, 120, 900), (180, 92, 300), (178, 120, 300), (0, 180, 1000)],
    "flick":        [(178, 110, 900), (180, 95, 250), (178, 150, 160), (150, 160, 500), (0, 180, 900)],
    "scoop":        [(180, 118, 900), (180, 96, 700), (150, 140, 600)],  # drag an object towards the bumper
    "push_ready":   [(180, 100, 900)],                                  # claw low: robot can push while driving
    "wave":         [(110, 120, 700), (110, 165, 250), (110, 120, 250), (110, 165, 250),
                     (110, 120, 250), (0, 180, 900)],
    "nod":          [(30, 170, 400), (10, 180, 300), (30, 170, 300), (0, 180, 400)],
    "shrug":        [(55, 140, 500), (35, 170, 500), (0, 180, 600)],
    "celebrate":    [(120, 150, 500), (140, 120, 200), (120, 150, 200), (140, 120, 200), (0, 180, 900)],
}

SKILL_HELP = {
    "park": "fold the arm into the roof bay (required before driving)",
    "raise": "hold the arm straight up like a periscope",
    "look_around": "raise, sweep and park - an expressive 'looking around' gesture",
    "point_forward": "point at something straight ahead",
    "hover": "hold the claw just above the floor ~12 cm in front of the bumper",
    "reach_floor": "put the claw on the floor in front (to touch / pin an object)",
    "tap": "tap an object on the floor in front, then park",
    "flick": "flick a light object (ball, paper) forward, then park",
    "scoop": "drag a small object towards the robot",
    "push_ready": "lower the claw so the robot can push an object while driving forward",
    "wave": "wave hello / goodbye",
    "nod": "small 'yes' nod",
    "shrug": "'I don't know' shrug",
    "celebrate": "happy celebration gesture",
}

# poses in which it is OK to drive (claw folded, or intentionally pushing)
DRIVE_SAFE = {"park", "push_ready"}


def clamp(v, lo, hi):
    return max(lo, min(hi, int(v)))


def tip_position(arm1, arm2):
    """Claw tip (y, z) in mm for given joint angles (useful for prompts / debugging)."""
    def d(phi):
        p = math.radians(phi)
        return (-math.cos(p), math.sin(p))
    a1 = math.radians(arm1)
    e = (SHOULDER[0] - L1 * math.cos(a1), SHOULDER[1] + L1 * math.sin(a1))
    dx, dz = d(arm1 + 180 - arm2)
    return (e[0] + L2 * dx, e[1] + L2 * dz)


def pose_is_safe(arm1, arm2):
    y, z = tip_position(arm1, arm2)
    inside_body = y < 104 and z < 98 and y > -100
    below_floor = z < 4
    return not inside_body and not below_floor


class Arm:
    def __init__(self, bridge_call, on_change=None):
        self.bridge_call = bridge_call
        self.on_change = on_change          # callback(arm1, arm2) to sync dashboard
        self.arm1, self.arm2 = PARK
        self.mode = "park"

    def move(self, arm1, arm2, ms=0):
        arm1 = clamp(arm1, *ARM1_RANGE)
        arm2 = clamp(arm2, *ARM2_RANGE)
        # never drive the claw into our own body or through the floor
        while arm2 < ARM2_RANGE[1] and not pose_is_safe(arm1, arm2):
            arm2 += 5
        self.bridge_call("armPose", f"{arm1},{arm2},{int(ms)}")
        self.arm1, self.arm2 = arm1, arm2
        if self.on_change:
            try:
                self.on_change(arm1, arm2)
            except Exception as e:  # pragma: no cover - dashboard sync is best effort
                logger.debug("arm on_change failed: %s", e)

    def run(self, name):
        frames = SKILLS.get(name)
        if not frames:
            logger.warning("Unknown arm skill: %s", name)
            return False
        logger.info("Arm skill: %s", name)
        for a1, a2, ms in frames:
            self.move(a1, a2, ms)
            time.sleep(0.05)
        self.mode = name if frames[-1][:2] != PARK else "park"
        return True

    def ensure_drive_safe(self):
        """Fold the arm before driving unless it was deliberately put in a pushing pose."""
        if self.mode in DRIVE_SAFE or (self.arm1, self.arm2) == PARK:
            return
        self.run("park")

    def describe(self):
        y, z = tip_position(self.arm1, self.arm2)
        return (f"arm1={self.arm1} arm2={self.arm2} mode={self.mode} "
                f"(claw tip ~{y:.0f} mm ahead of body centre, {z:.0f} mm above floor; bumper at 100 mm)")


def skills_prompt():
    lines = [f"  - {k}: {v}" for k, v in SKILL_HELP.items()]
    return "\n".join(lines)
