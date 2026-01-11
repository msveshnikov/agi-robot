from arduino.app_utils import App
from arduino.app_utils import Bridge
from arduino.app_bricks.web_ui import WebUI
from arduino.app_bricks.video_objectdetection import VideoObjectDetection
from datetime import datetime, UTC
from arduino.app_bricks.arduino_cloud import ArduinoCloud
from arduino.app_peripherals.microphone import Microphone

import urllib.request
import urllib.parse
import os
import logging
import io
import base64
import json
import time
import colorsys
import wave
     
ui = WebUI()
detection_stream = VideoObjectDetection(confidence=0.5, debounce_sec=0.0)
ui.on_message("override_th", lambda sid, threshold: detection_stream.override_threshold(threshold))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("robot.main")

MAIN_GOAL = "Be helpful assistant to the master human"

def send_detections_to_ui(detections: dict):
  for key, value in detections.items():
    entry = {
      "content": key,
      "confidence": value.get("confidence"),
      "timestamp": datetime.now(UTC).isoformat()
    }
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

lang = "en"

def lang_callback(client: object, value: str):
    global lang
    logger.info(f"Language updated from cloud: {value}")
    lang = value
    try:
        speak(f"Language changed to {value}")
    except Exception:
        pass

rgb = "255,0,255"
rgb_values = {"hue": 0, "sat": 0, "bri": 0, "swi": False}

def update_rgb_from_values():
    global rgb
    try:
        swi = rgb_values.get("swi", False)
        if isinstance(swi, str):
            swi = (swi.lower() == "true")
        
        if not swi:
            rgb = "0,0,0"
        else:
            h = float(rgb_values.get("hue", 0)) / 360.0
            s = float(rgb_values.get("sat", 0)) / 100.0
            v = float(rgb_values.get("bri", 0)) / 100.0
            
            r_float, g_float, b_float = colorsys.hsv_to_rgb(h, s, v)
            rgb = f"{int(r_float * 255)},{int(g_float * 255)},{int(b_float * 255)}"
            
        logger.info(f"Updated RGB string: {rgb} from {rgb_values}")
    except Exception as e:
        logger.error(f"Error calculating RGB: {e}")

def rgb_hue_callback(client: object, value):
    logger.info(f"RGB Hue update: {value}")
    rgb_values["hue"] = value
    update_rgb_from_values()

def rgb_sat_callback(client: object, value):
    logger.info(f"RGB Sat update: {value}")
    rgb_values["sat"] = value
    update_rgb_from_values()

def rgb_bri_callback(client: object, value):
    logger.info(f"RGB Bri update: {value}")
    rgb_values["bri"] = value
    update_rgb_from_values()

def rgb_swi_callback(client: object, value):
    logger.info(f"RGB Swi update: {value}")
    rgb_values["swi"] = value
    update_rgb_from_values()

arduino_cloud.register("speed", on_write=speed_callback)
arduino_cloud.register("back",  on_write=back_callback)
arduino_cloud.register("left",  on_write=left_callback)
arduino_cloud.register("right", on_write=right_callback)
arduino_cloud.register("forward", on_write=forward_callback)
arduino_cloud.register("agi", on_write=agi_callback)
arduino_cloud.register("goal", on_write=goal_callback)
arduino_cloud.register("lang", on_write=lang_callback)

# Register individual RGB callbacks
arduino_cloud.register("rgb:hue", on_write=rgb_hue_callback)
arduino_cloud.register("rgb:sat", on_write=rgb_sat_callback)
arduino_cloud.register("rgb:bri", on_write=rgb_bri_callback)
arduino_cloud.register("rgb:swi", on_write=rgb_swi_callback)

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

def get_rgb():
    return rgb

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

def play_random_sound():
    try:
        url = f"http://172.17.0.1:5000/play_random"
        with urllib.request.urlopen(url, timeout=55) as response:
            logger.info(f"Random sound service called: {response.read().decode()}")
    except Exception as e:
        logger.warning(f"Could not call random sound service: {e}")


def speak(text):
    try:
        query = urllib.parse.urlencode({'text': text, 'lang': lang})
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
Bridge.provide("get_rgb", get_rgb)
Bridge.provide("set_distance", set_distance)

def set_temperature(t):
  arduino_cloud.temperature = t

def set_humidity(h):
  arduino_cloud.humidity = h

Bridge.provide("set_temperature", set_temperature)
Bridge.provide("set_humidity", set_humidity)

play_sound("python/sounds/startup.wav")
speak("Robot is ready")

def ask_llm_vision(distance: float, plan: str = "", subplan: str = "", movement_history: list = None, space_map: str = "", memory: str = "") -> dict:
    """Call the /llm_vision endpoint, sending distance, plan, subplan, map, and audio if available. Returns parsed JSON dict or {}."""
    try:
        if movement_history is None:
            movement_history = []
        payload = {
            "distance": distance,
            "plan": plan,
            "subplan": subplan,
            "map": space_map,
            "memory": memory,
            "main_goal": MAIN_GOAL,
            "movement_history": movement_history,
            "lang": lang
        }
        
        # Include mic.wav if it exists
        if os.path.exists("mic.wav"):
            try:
                with open("mic.wav", "rb") as audio_file:
                    audio_data = audio_file.read()
                    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                    payload["audio"] = audio_base64
                    payload["audio_format"] = "wav"
                    logger.info("Including mic.wav in llm_vision request")
                # Delete the file after reading it
                os.remove("mic.wav")
                logger.info("Deleted mic.wav after inclusion in payload")
            except Exception as audio_err:
                logger.warning(f"Could not read/delete mic.wav: {audio_err}")
        
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
plan = ""
subplan = ""
space_map = ""
movement_history = []
memory = ""

MEMORY_FILE = "memory.txt"

def load_memory():
    global memory
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                memory = f.read()
            logger.info("Memory loaded from %s", MEMORY_FILE)
        except Exception as e:
            logger.warning("Could not load memory: %s", e)

def save_memory(new_memory):
    global memory
    memory = new_memory
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            f.write(memory)
        logger.info("Memory saved to %s", MEMORY_FILE)
    except Exception as e:
        logger.warning("Could not save memory: %s", e)

load_memory()

def agi_loop(distance):
    """Called from MCU. Sends distance + subplan to LLM-vision, handles JSON response.

    {
      "speak": {"text": "...",
      "sound": "casual",
      "move": {"command": "forward|back|left|right|stop",  "distance_cm": integer, "angle_deg": integer },
      "plan": "updated global strategy",
      "subplan": "updated context string",
      "map": "updated map string",
      "memory": "updated memory string"
    }
    """
    
    
    global plan, subplan, space_map, memory, forward, back, left, right, movement_history, rgb
    logger.info(f"AGI loop called with distance: {distance}, plan: {plan}, subplan: {subplan}, memory size: {len(memory)}")

    resp = ask_llm_vision(distance=distance, plan=plan, subplan=subplan, movement_history=movement_history, space_map=space_map, memory=memory)
    move_cmd = ""
    if not resp:
        return move_cmd

    # Update state if provided
    try:
        if "plan" in resp and isinstance(resp["plan"], str):
            plan = resp["plan"]
        if "subplan" in resp and isinstance(resp["subplan"], str):
            subplan = resp["subplan"]
        if "map" in resp and isinstance(resp["map"], str):
            space_map = resp["map"]
        if "memory" in resp and isinstance(resp["memory"], str):
            save_memory(resp["memory"])
    except Exception:
        pass

    # Handle speaking
    try:
        sp = resp.get("speak")
        if sp and isinstance(sp, dict):
            text = sp.get("text")
            if text:
                speak(text)
                logger.info("Robot speaking!! Starting 10-second recording...")
    
                # now record mic for 5 sec and save to file with proper WAV header
                mic = Microphone()
                mic.start()
                try:
                    audio_chunk_iterator = mic.stream()  # Returns a numpy array iterator
                    start_time = time.time()
                    
                    # Use wave module to write with header
                    with wave.open("mic.wav", "wb") as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2) # S16_LE is 2 bytes
                        wf.setframerate(16000)
                        
                        for chunk in audio_chunk_iterator:
                            wf.writeframes(chunk.tobytes())
                            if time.time() - start_time >= 5:
                                break
                    logger.info("Recording finished and saved to mic.wav with WAV header")
                finally:
                    mic.stop()
                  
    except Exception as e:
        logger.warning("Warning handling speak: %s", e)

    # Handle sound
    try:
        snd = resp.get("sound")
        if snd == "casual":
             play_random_sound()
    except Exception as e:
        logger.warning("Warning handling sound: %s", e)

    # Handle RGB
    try:
        rgb_val = resp.get("rgb")
        if rgb_val and isinstance(rgb_val, str):
            # Validate format "R,G,B"
            parts = rgb_val.split(',')
            if len(parts) == 3:
                 rgb = rgb_val
                 logger.info(f"AGI set RGB to: {rgb}")
    except Exception as e:
        logger.warning("Warning handling rgb: %s", e)


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
