from arduino.app_utils import App
from arduino.app_utils import Bridge
from arduino.app_bricks.web_ui import WebUI
from arduino.app_bricks.video_objectdetection import VideoObjectDetection
from datetime import datetime, UTC
from arduino.app_bricks.arduino_cloud import ArduinoCloud
import urllib.request
import urllib.parse
import os
import logging
import io
import base64
import json
import time
     
ui = WebUI()
detection_stream = VideoObjectDetection(confidence=0.5, debounce_sec=0.0)
ui.on_message("override_th", lambda sid, threshold: detection_stream.override_threshold(threshold))

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("robot.main")

last_speak_time = 0
# Persistent main goal (remains for the robot forever)
MAIN_GOAL = "Find the Christmas Tree in the room"

# Control talkative behavior: announce intentions often
last_intent_speak_time = 0

def send_detections_to_ui(detections: dict):
  global last_speak_time
  for key, value in detections.items():
    entry = {
      "content": key,
      "confidence": value.get("confidence"),
      "timestamp": datetime.now(UTC).isoformat()
    }
    
    # if time.time() - last_speak_time >= 10:
    #     speak(key)
    #     last_speak_time = time.time()

    ui.send_message("detection", message=entry)
 
detection_stream.on_detect_all(send_detections_to_ui)

arduino_cloud = ArduinoCloud()
speed = 0
back = False
left = False
right = False
forward = False
agi = False

def speed_callback(client: object, value: int):
    global speed
    logger.info(f"Speed value updated from cloud: {value}")
    speed = value

def back_callback(client: object, value: bool):
    global back
    logger.info(f"Back value updated from cloud: {value}")
    back = value

def left_callback(client: object, value: bool):
    global left
    logger.info(f"Left value updated from cloud: {value}")
    left = value

def right_callback(client: object, value: bool):
    global right
    logger.info(f"Right value updated from cloud: {value}")
    right = value

def forward_callback(client: object, value: bool):
    global forward
    logger.info(f"Forward value updated from cloud: {value}")
    forward = value

def agi_callback(client: object, value: bool):
    global agi
    logger.info(f"AGI value updated from cloud: {value}")
    agi = value

def goal_callback(client: object, value: str):
    global MAIN_GOAL
    logger.info(f"Main Goal updated from cloud: {value}")
    MAIN_GOAL = value
    try:
        speak(f"New goal received: {value}")
    except Exception:
        pass

arduino_cloud.register("speed", on_write=speed_callback)
arduino_cloud.register("back",  on_write=back_callback)
arduino_cloud.register("left",  on_write=left_callback)
arduino_cloud.register("right", on_write=right_callback)
arduino_cloud.register("forward", on_write=forward_callback)
arduino_cloud.register("agi", on_write=agi_callback)
arduino_cloud.register("goal", on_write=goal_callback)
arduino_cloud.register("distance")
arduino_cloud.register("temperature")
arduino_cloud.register("humidity")

def get_speed():
    return speed

def get_back():
    return back

def get_left():
    return left

def get_right():
    return right

def get_forward():
    return forward

def get_agi():
    return agi

def set_distance(d):
    arduino_cloud.distance = int(d)

def play_sound(filename):
    try:
        query = urllib.parse.urlencode({'filename': filename})
        url = f"http://172.17.0.1:5000/play?{query}"
        with urllib.request.urlopen(url, timeout=55) as response:
            logger.info(f"Sound service called: {response.read().decode()}")
    except Exception as e:
        logger.warning(f"Could not call sound service: {e}")

def speak(text):
    try:
        query = urllib.parse.urlencode({'text': text})
        url = f"http://172.17.0.1:5000/speak?{query}"
        with urllib.request.urlopen(url, timeout=55) as response:
            logger.info(f"Speak service called: {response.read().decode()}")
    except Exception as e:
        logger.warning(f"Could not call speak service: {e}")


Bridge.provide("play_sound", play_sound)
Bridge.provide("speak", speak)
Bridge.provide("get_speed", get_speed)
Bridge.provide("get_back", get_back)
Bridge.provide("get_left", get_left)
Bridge.provide("get_right", get_right)
Bridge.provide("get_forward", get_forward)
Bridge.provide("get_agi", get_agi)
Bridge.provide("set_distance", set_distance)

def set_temperature(t):
  arduino_cloud.temperature = t

def set_humidity(h):
  arduino_cloud.humidity = h

Bridge.provide("set_temperature", set_temperature)
Bridge.provide("set_humidity", set_humidity)

play_sound("/home/arduino/1.wav")
speak("Robot is ready")
try:
    speak(f"My main goal is to {MAIN_GOAL}.")
except Exception:
    pass


def ask_llm_vision(distance: float, subplan: str = "", movement_history: list = None) -> dict:
    """Call the /llm_vision endpoint, sending distance and subplan. Returns parsed JSON dict or {}."""
    try:
        if movement_history is None:
            movement_history = []
        payload = {"distance": distance, "subplan": subplan, "main_goal": MAIN_GOAL, "movement_history": movement_history}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(f"http://172.17.0.1:5000/llm_vision", data=data, headers={"Content-Type":"application/json"})
        with urllib.request.urlopen(req, timeout=55) as response:
            resp = response.read().decode("utf-8")
            try:
                return json.loads(resp)
            except Exception:
                logger.warning("llm_vision returned non-json, raw: %s", resp)
                return {}
    except Exception as e:
        logger.warning(f"Could not call LLM vision service: {e}")
        return {}

# Internal subplan/context for AGI loop
subplan = ""
movement_history = []


def agi_loop(distance):
    """Called from MCU. Sends distance + subplan to LLM-vision, handles JSON response.

    Expected JSON schema:
    {
      "speak": {"text": "...",
      "move": {"command": "forward|back|left|right|stop",  "distance_cm": integer, "angle_deg": integer },
      "subplan": "updated context string"
    }
    """
    
    
    global subplan, forward, back, left, right, movement_history
    logger.info(f"AGI loop called with distance: {distance}, current subplan: {subplan}")

    resp = ask_llm_vision(distance=distance, subplan=subplan, movement_history=movement_history)
    move_cmd = ""
    if not resp:
        return move_cmd

    # Update subplan if provided
    try:
        if "subplan" in resp and isinstance(resp["subplan"], str):
            subplan = resp["subplan"]
    except Exception:
        pass

    # Handle speaking
    try:
        sp = resp.get("speak")
        if sp and isinstance(sp, dict):
            text = sp.get("text")
            if text:
                speak(text)
    except Exception as e:
        logger.warning("Warning handling speak: %s", e)

    # Handle movement: build a short command string for MCU to execute and return it
    try:
        mv = resp.get("move")
        if mv and isinstance(mv, dict):
            # Expected keys: command (forward|back|left|right), distance_cm, angle_deg
            cmd = mv.get("command")
            mv_distance = mv.get("distance_cm")
            angle = mv.get("angle_deg")
            chosen_speed = 50
            if cmd in ("forward", "back") and mv_distance is not None:
                # Format: MOVE|direction|distance_cm|speed
                move_cmd = f"MOVE|{cmd}|{int(mv_distance)}|{chosen_speed}"
            elif cmd in ("left", "right") and angle is not None:
                # Format: TURN|direction|angle_deg|speed
                move_cmd = f"TURN|{cmd}|{int(angle)}|{chosen_speed}"
            elif cmd == "stop":
                move_cmd = "STOP"
            
            # Add to history if a valid move command was generated
            if move_cmd:
                movement_history.append(mv)

    except Exception as e:
        logger.warning("Warning handling move: %s", e)

    return move_cmd


# expose agi_loop to the MCU
Bridge.provide("agi_loop", agi_loop)
App.start_brick(arduino_cloud)

App.run()
