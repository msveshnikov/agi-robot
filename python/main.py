from arduino.app_utils import App
from arduino.app_utils import Bridge
from arduino.app_bricks.web_ui import WebUI
from arduino.app_bricks.video_objectdetection import VideoObjectDetection
from datetime import datetime, UTC
from backend_client import BackendClient
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
import threading
     
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

BACKEND_URL = os.environ.get("BACKEND_URL", "https://robot.mvpgen.com")
arduino_cloud = BackendClient(BACKEND_URL)
speed = 0
back = False
left = False
right = False
forward = False
panic= False
agi = False
asi = False
alarm = False
lang = "en"
rgb = "255,0,255"
arm1 = 0
arm2 = 0


def speed_callback(client: object, value: int):
    global speed
    logger.info(f"Speed value updated from cloud: {value}")
    speed = value

def panic_callback(client: object, value: bool):
    global panic
    logger.info(f"Panic value updated from cloud: {value}")
    panic = value

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

def asi_callback(client: object, value: bool):
    global asi
    logger.info(f"ASI value updated from cloud: {value}")
    asi = value

def goal_callback(client: object, value: str):
    global MAIN_GOAL
    logger.info(f"Main Goal updated from cloud: {value}")
    MAIN_GOAL = value
    try:
        speak(f"New goal received: {value}")
    except Exception:
        pass


def lang_callback(client: object, value: str):
    global lang
    logger.info(f"Language updated from cloud: {value}")
    lang = value
    try:
        speak(f"Language changed to {value}")
    except Exception:
        pass

def arm1_callback(client, value):
    global arm1
    logger.info(f"Arm1 value updated from cloud: {value}")
    try:
        arm1 = int(value)
        Bridge.call("setArm1", arm1)
    except Exception as e:
        logger.error(f"Error handling Arm1 update: {e}")

def arm2_callback(client, value):
    global arm2
    logger.info(f"Arm2 value updated from cloud: {value}")
    try:
        arm2 = int(value)
        Bridge.call("setArm2", arm2)
    except Exception as e:
        logger.error(f"Error handling Arm2 update: {e}")

def rgb_callback(client: object, value):
    """Callback function to handle RGB light updates from cloud."""
    global rgb
    try:
        # value has properties: hue, sat, bri, swi (from MockValue or dict proxy)
        swi = getattr(value, 'swi', True)
        if isinstance(swi, str):
            swi = (swi.lower() == "true")
        
        if not swi:
            rgb = "0,0,0"
        else:
            h = float(getattr(value, 'hue', 0)) / 360.0
            s = float(getattr(value, 'sat', 0)) / 100.0
            v = float(getattr(value, 'bri', 100)) / 100.0
            
            r_float, g_float, b_float = colorsys.hsv_to_rgb(h, s, v)
            rgb = f"{int(r_float * 255)},{int(g_float * 255)},{int(b_float * 255)}"
            
        logger.info(f"RGB value updated from backend: {rgb}")
        Bridge.notify("setRGB", rgb)
    except Exception as e:
        logger.error(f"Error handling RGB update: {e}")

# Rainbow effect for listening mode
rainbow_stop_event = None
rainbow_thread = None

def rainbow_effect(stop_event, interval=0.1):
    """Cycles through rainbow colors on the RGB LED until stop_event is set."""
    hue = 0.0
    while not stop_event.is_set():
        # Convert HSV to RGB (full saturation and brightness)
        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        rgb_string = f"{int(r * 255)},{int(g * 255)},{int(b * 255)}"
        
        try:
            Bridge.notify("setRGB", rgb_string)
        except Exception as e:
            logger.warning(f"Error setting RGB during rainbow: {e}")
        
        # Increment hue (wrap around at 1.0)
        hue = (hue + 0.02) % 1.0
        time.sleep(interval)
    
    # When stopping, turn off LED
    try:
        Bridge.notify("setRGB", "0,0,0")
    except Exception:
        pass

def rainbow_while_listening():
    """Start a background rainbow effect. Returns a stop function to call when done."""
    global rainbow_stop_event, rainbow_thread
    
    # Stop any existing rainbow
    if rainbow_stop_event and rainbow_thread:
        rainbow_stop_event.set()
        rainbow_thread.join(timeout=1.0)
    
    # Start new rainbow effect
    rainbow_stop_event = threading.Event()
    rainbow_thread = threading.Thread(target=rainbow_effect, args=(rainbow_stop_event,), daemon=True)
    rainbow_thread.start()
    logger.info("Rainbow effect started")
    
    def stop_rainbow():
        global rainbow_stop_event, rainbow_thread
        if rainbow_stop_event:
            rainbow_stop_event.set()
            if rainbow_thread:
                rainbow_thread.join(timeout=1.0)
            logger.info("Rainbow effect stopped")
            Bridge.notify("setRGB", rgb)
    
    return stop_rainbow


arduino_cloud.register("speed", on_write=speed_callback)
arduino_cloud.register("panic", on_write=panic_callback)
arduino_cloud.register("back",  on_write=back_callback)
arduino_cloud.register("left",  on_write=left_callback)
arduino_cloud.register("right", on_write=right_callback)
arduino_cloud.register("forward", on_write=forward_callback)
arduino_cloud.register("agi", on_write=agi_callback)
arduino_cloud.register("asi", on_write=asi_callback)
arduino_cloud.register("goal", on_write=goal_callback)
arduino_cloud.register("lang", on_write=lang_callback)
arduino_cloud.register("arm1", on_write=arm1_callback)
arduino_cloud.register("arm2", on_write=arm2_callback)

# Register RGB
arduino_cloud.register("rgb", on_write=rgb_callback)
arduino_cloud.register("distance")
arduino_cloud.register("temperature")
arduino_cloud.register("humidity")
arduino_cloud.register("plan")
arduino_cloud.register("subplan")
arduino_cloud.register("space_map")
arduino_cloud.register("movement_history")
arduino_cloud.register("memory")
arduino_cloud.register("alarm")

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
    if lang == "disabled":
        return
    try:
        query = urllib.parse.urlencode({'text': text, 'lang': lang})
        url = f"http://172.17.0.1:5000/speak?{query}"
        with urllib.request.urlopen(url, timeout=55) as response:
            logger.info(f"Speak service called: {response.read().decode()}")
    except Exception as e:
        logger.warning(f"Could not call speak service: {e}")


def set_distance(d):
  arduino_cloud.distance = int(d)

def set_temperature(t):
  arduino_cloud.temperature = t

def set_humidity(h):
  arduino_cloud.humidity = h

Bridge.provide("set_temperature", set_temperature)
Bridge.provide("set_humidity", set_humidity)
Bridge.provide("set_distance", set_distance)

def play_random_sound_callback(value):
    play_random_sound()
    
Bridge.provide("play_random_sound", play_random_sound_callback)

play_sound("/home/arduino/ArduinoApps/robot/python/sounds/startup.wav")
speak("Robot is ready")

def ask_llm_vision(distance: float, temperature: float = None, humidity: float = None, plan: str = "", subplan: str = "", movement_history: list = None, space_map: str = "", memory: str = "", arm1: int = 0, arm2: int = 0) -> dict:
    """Call the /llm_vision endpoint, sending distance, plan, subplan, space_map, and audio if available. Returns parsed JSON dict or {}."""
    try:
        if movement_history is None:
            movement_history = []
        payload = {
            "distance": distance,
            "temperature": temperature,
            "humidity": humidity,
            "plan": plan,
            "subplan": subplan,
            "space_map": space_map,
            "memory": memory,
            "main_goal": MAIN_GOAL,
            "movement_history": movement_history,
            "lang": lang,
            "asi": asi,
            "arm1": arm1,
            "arm2": arm2
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

def agi_loop():
    """Called from MCU. Sends distance + subplan to LLM-vision, handles JSON response.

    {
      "speak": {"text": "..."},
      "sound": "casual",
      "moves": [{"command": "forward|back|left|right|stop", "distance_cm": integer, "angle_deg": integer}, ...],
      "plan": "updated global strategy",
      "subplan": "updated context string",
      "space_map": "updated map string",
      "memory": "updated memory string",
      "alarm": "alarm message if needed"
    }
    """
    
    distance = Bridge.call("getDistance")
    temperature = getattr(arduino_cloud, 'temperature', None)
    humidity = getattr(arduino_cloud, 'humidity', None)

    global plan, subplan, space_map, memory, forward, back, left, right, movement_history, rgb, alarm, arm1, arm2
    logger.info(f"AGI loop called with distance: {distance}, temp: {temperature}, hum: {humidity}, plan: {plan}, subplan: {subplan}, memory size: {len(memory)}")

    resp = ask_llm_vision(distance=distance, temperature=temperature, humidity=humidity, plan=plan, subplan=subplan, movement_history=movement_history, space_map=space_map, memory=memory, arm1=arm1, arm2=arm2)
    
    if not resp:
        return

    # Update state if provided
    try:
        if "plan" in resp and isinstance(resp["plan"], str):
            plan = resp["plan"]
        if "subplan" in resp and isinstance(resp["subplan"], str):
            subplan = resp["subplan"]
        if "space_map" in resp and isinstance(resp["space_map"], str):
            space_map = resp["space_map"]
        if "memory" in resp and isinstance(resp["memory"], str):
            save_memory(resp["memory"])
        if "alarm" in resp:
            alarm = resp["alarm"]
    except Exception:
        pass

    # Handle RGB
    try:
        rgb_val = resp.get("rgb")
        if rgb_val and isinstance(rgb_val, str):
            # Validate format "R,G,B"
            parts = rgb_val.split(',')
            if len(parts) == 3:
                 rgb = rgb_val
                 logger.info(f"AGI set RGB to: {rgb}")
        Bridge.notify("setRGB", rgb)
    except Exception as e:
        logger.warning("Warning handling rgb: %s", e)

    # Handle Arm
    try:
        if "arm1" in resp and resp["arm1"] is not None:
             val = int(resp["arm1"])
             arm1 = val # Update global variable
             arduino_cloud.arm1 = val
             Bridge.call("setArm1", val)
             logger.info(f"AGI set Arm1 to: {val}")
        
        if "arm2" in resp and resp["arm2"] is not None:
             val = int(resp["arm2"])
             arm2 = val # Update global variable
             arduino_cloud.arm2 = val
             Bridge.call("setArm2", val)
             logger.info(f"AGI set Arm2 to: {val}")
    except Exception as e:
        logger.warning("Warning handling arm: %s", e)

    # Handle sound
    try:
        snd = resp.get("sound")
        if snd == "casual":
             play_random_sound()
    except Exception as e:
        logger.warning("Warning handling sound: %s", e)


    # Handle movement: process array of movement commands
    try:
        moves = resp.get("moves")
        if moves and isinstance(moves, list):
            # Process each movement command in sequence
            for idx, mv in enumerate(moves):
                if not isinstance(mv, dict):
                    logger.warning(f"Move command at index {idx} is not a dict, skipping")
                    continue
                
                # Expected keys: command (forward|back|left|right), distance_cm, angle_deg
                cmd = mv.get("command")
                mv_distance = mv.get("distance_cm")
                angle = mv.get("angle_deg")
                chosen_speed = speed
                move_cmd = None
                
                if cmd in ("forward", "back") and mv_distance is not None:
                    # Format: MOVE|direction|distance_cm|speed
                    move_cmd = f"MOVE|{cmd}|{int(mv_distance)}|{chosen_speed}"
                elif cmd in ("left", "right") and angle is not None:
                    # Format: TURN|direction|angle_deg|speed
                    move_cmd = f"TURN|{cmd}|{int(angle)}|{chosen_speed}"
                elif cmd == "stop":
                    move_cmd = "STOP"
                
                # Execute the move command and wait for completion
                if move_cmd:
                    logger.info(f"Executing move {idx + 1}/{len(moves)}: {move_cmd}")
                    # Add to history
                    movement_history.append(mv)
                    # Execute the command and wait (stop=True for all but the last command)
                    is_last_move = (idx == len(moves) - 1)
                    Bridge.call("move", move_cmd, True)
                    
                    # Add a small delay between moves for stability
                    if not is_last_move:
                        time.sleep(0.2)
        
        # Also support single 'move' command for backward compatibility
        elif "move" in resp:
            mv = resp.get("move")
            if mv and isinstance(mv, dict):
                # Expected keys: command (forward|back|left|right), distance_cm, angle_deg
                cmd = mv.get("command")
                mv_distance = mv.get("distance_cm")
                angle = mv.get("angle_deg")
                chosen_speed = speed
                move_cmd = None
                
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
                    Bridge.notify("move", move_cmd, True)
    except Exception as e:
        logger.warning("Warning handling move: %s", e)

    # Handle speaking
    try:
        sp = resp.get("speak")
        if sp and isinstance(sp, dict):
            text = sp.get("text")
            if text and lang != "disabled":
                speak(text)
                logger.info("Robot spoke!! Starting dynamic recording (up to 15 seconds)...")
    
                # Start rainbow effect while listening
                stop_rainbow = rainbow_while_listening()
                
                # Record mic with dynamic duration extension based on audio level
                mic = Microphone()
                mic.start()
                try:
                    import numpy as np
                    
                    audio_chunk_iterator = mic.stream()  # Returns a numpy array iterator
                    start_time = time.time()
                    max_duration = 15  # Maximum recording duration in seconds
                    min_duration = 3   # Initial recording duration
                    current_max = min_duration
                    last_second_chunks = []
                    
                    # Use wave module to write with header
                    with wave.open("mic.wav", "wb") as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2) # S16_LE is 2 bytes
                        wf.setframerate(16000)
                        
                        for chunk in audio_chunk_iterator:
                            wf.writeframes(chunk.tobytes())
                            elapsed = time.time() - start_time
                            
                            # Keep track of chunks in the last second
                            last_second_chunks.append(chunk)
                            
                            # Check if we've reached the current maximum duration
                            if elapsed >= current_max:
                                # Calculate audio level for the last second
                                if last_second_chunks:
                                    # Combine all chunks from the last second
                                    last_second_audio = np.concatenate(last_second_chunks)
                                    
                                    # Calculate RMS (Root Mean Square) and convert to dB
                                    rms = np.sqrt(np.mean(last_second_audio.astype(np.float32)**2))
                                    # Convert to dB (reference: max value for int16)
                                    if rms > 0:
                                        db_level = 20 * np.log10(rms / 32768.0) + 90  # Normalize to ~0-90 dB range
                                    else:
                                        db_level = 0
                                    
                                    logger.info(f"Audio level at {elapsed:.1f}s: {db_level:.1f} dB")
                                    
                                    # If last second was not silent (>45 dB) and we haven't reached max, extend by 1 second
                                    if db_level > 45 and current_max < max_duration:
                                        current_max += 1
                                        logger.info(f"Audio detected, extending recording to {current_max} seconds")
                                        last_second_chunks = []  # Reset for next second
                                    else:
                                        # Either silent or reached max duration
                                        if db_level <= 45:
                                            logger.info("Silence detected, stopping recording")
                                        break
                                else:
                                    break
                            
                            # Keep only the last second worth of chunks (approximately)
                            # Assuming chunks are small, keep last ~50 chunks (rough estimate)
                            if len(last_second_chunks) > 50:
                                last_second_chunks.pop(0)
                    
                    logger.info(f"Recording finished after {time.time() - start_time:.1f} seconds and saved to mic.wav")
                finally:
                    mic.stop()
                    # Stop rainbow effect when recording is done
                    stop_rainbow()
                    logger.info("Rainbow effect stopped after recording")
                  
    except Exception as e:
        logger.warning("Warning handling speak: %s", e)

    # Sync variables to Arduino Cloud
    try:
        arduino_cloud.plan = plan
        arduino_cloud.subplan = subplan
        arduino_cloud.space_map = space_map
        arduino_cloud.movement_history = json.dumps(movement_history)
        arduino_cloud.memory = memory
        arduino_cloud.alarm = alarm
        logger.info("Synced variables to Arduino Cloud")
    except Exception as e:
        logger.warning(f"Error syncing to cloud: {e}")

def loop():
    global speed, back, left, right, forward, agi, panic
    try:
        
        if left:
            Bridge.call("move", f"TURN|left|20|{speed}", False)
        elif right:
            Bridge.call("move", f"TURN|right|20|{speed}", False)
        elif forward:
            Bridge.call("move", f"MOVE|forward|20|{speed}", False)
        elif back:
            Bridge.call("move", f"MOVE|back|20|{speed}", False)
        elif panic:
            Bridge.call("panic", speed)
        elif agi:
            agi_loop()
        else:
            Bridge.call("move", "STOP", True)
        
        time.sleep(0.1)

    except Exception as e:
        logger.error(f"Error in main loop: {e}")    

# App.start_brick(arduino_cloud) # Removed Arduino Cloud brick
arduino_cloud.start()
App.run(user_loop=loop)
