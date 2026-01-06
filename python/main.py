from arduino.app_utils import App
from arduino.app_utils import Bridge
from arduino.app_bricks.web_ui import WebUI
from arduino.app_bricks.video_objectdetection import VideoObjectDetection
from datetime import datetime, UTC
from arduino.app_bricks.arduino_cloud import ArduinoCloud
import urllib.request
import urllib.parse
import os
from arduino.app_bricks.keyword_spotting import KeywordSpotting

from arduino.app_peripherals.usb_camera import USBCamera
from PIL.Image import Image
import io
import base64
import json
     

ui = WebUI()
detection_stream = VideoObjectDetection(confidence=0.5, debounce_sec=0.0)

ui.on_message("override_th", lambda sid, threshold: detection_stream.override_threshold(threshold))


import time

last_speak_time = 0

def send_detections_to_ui(detections: dict):
  global last_speak_time
  for key, value in detections.items():
    entry = {
      "content": key,
      "confidence": value.get("confidence"),
      "timestamp": datetime.now(UTC).isoformat()
    }
    
    if time.time() - last_speak_time >= 10:
        speak(key)
        last_speak_time = time.time()

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
    print(f"Speed value updated from cloud: {value}")
    speed = value

def back_callback(client: object, value: bool):
    global back
    print(f"Speed value updated from cloud: {value}")
    back = value

def left_callback(client: object, value: bool):
    global left
    print(f"Left value updated from cloud: {value}")
    left = value

def right_callback(client: object, value: bool):
    global right
    print(f"Right value updated from cloud: {value}")
    right = value

def forward_callback(client: object, value: bool):
    global forward
    print(f"Forward value updated from cloud: {value}")
    forward = value

def agi_callback(client: object, value: bool):
    global agi
    print(f"AGI value updated from cloud: {value}")
    agi = value

arduino_cloud.register("speed", value=0, on_write=speed_callback)
arduino_cloud.register("back", value=False, on_write=back_callback)
arduino_cloud.register("left", value=False, on_write=left_callback)
arduino_cloud.register("right", value=False, on_write=right_callback)
arduino_cloud.register("forward", value=False, on_write=forward_callback)
arduino_cloud.register("agi", value=False, on_write=agi_callback)
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
        with urllib.request.urlopen(url, timeout=1) as response:
            print(f"Sound service called: {response.read().decode()}")
    except Exception as e:
        print(f"Warning: Could not call sound service: {e}")

def speak(text):
    try:
        query = urllib.parse.urlencode({'text': text})
        url = f"http://172.17.0.1:5000/speak?{query}"
        with urllib.request.urlopen(url, timeout=5) as response: # Increased timeout for TTS generation
            print(f"Speak service called: {response.read().decode()}")
    except Exception as e:
        print(f"Warning: Could not call speak service: {e}")

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
speak("Робот готов к бою!")

App.start_brick(arduino_cloud)

def ask_llm(prompt):
    try:
        query = urllib.parse.urlencode({'text': prompt})
        # Increase timeout for LLM generation
        url = f"http://172.17.0.1:5000/llm?{query}"
        with urllib.request.urlopen(url, timeout=15) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Warning: Could not call LLM service: {e}")
        return None


def ask_llm_vision(distance: float, subplan: str = "") -> dict:
    """Call the /llm_vision endpoint, sending distance and subplan. Returns parsed JSON dict or {}."""
    try:
        payload = {"distance": distance, "subplan": subplan}
        # try to attach a camera image if available
        try:
            cam = USBCamera()
            img = cam.capture()
            buf = io.BytesIO()
            img.save(buf, format="JPEG")
            img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            payload["image_base64"] = img_b64
        except Exception:
            pass

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(f"http://172.17.0.1:5000/llm_vision", data=data, headers={"Content-Type":"application/json"})
        with urllib.request.urlopen(req, timeout=20) as response:
            resp = response.read().decode("utf-8")
            try:
                return json.loads(resp)
            except Exception:
                print("Warning: llm_vision returned non-json, raw:", resp)
                return {}
    except Exception as e:
        print(f"Warning: Could not call LLM vision service: {e}")
        return {}

is_telling_anecdote = False

def on_keyword_detected():
    """Callback function that handles a detected keyword."""
    global is_telling_anecdote
    if is_telling_anecdote:
        print("Already telling an anecdote, skipping.")
        return

    print("Keyword detected! Asking LLM...")
    play_sound("/home/arduino/2.wav")

    is_telling_anecdote = True
    try:
        prompt = "Расскажи короткий смешной анекдот про сериал Очень Странные Дела"
        response = ask_llm(prompt)
        if response:
            print(f"LLM Response: {response}")
            speak(response)
        else:
            speak("Что-то пошло не так с моим электронным мозгом.")
    finally:
        is_telling_anecdote = False

spotter = KeywordSpotting()
spotter.on_detect("hey_arduino", on_keyword_detected)

App.run()

# Internal subplan/context for AGI loop
subplan = ""


def agi_loop(distance):
    """Called from MCU. Sends distance + subplan to LLM-vision, handles JSON response.

    Expected JSON schema:
    {
      "speak": {"text": "...",
      "move": {"command": "forward|back|left|right|stop", "duration": seconds, "speed": int},
      "subplan": "updated context string"
    }
    """
    global subplan, forward, back, left, right

    resp = ask_llm_vision(distance=distance, subplan=subplan)
    if not resp:
        return

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
        print("Warning handling speak:", e)

    # Handle movement: build a short command string for MCU to execute and return it
    move_cmd = ""
    try:
        mv = resp.get("move")
        if mv and isinstance(mv, dict):
            # Expected keys: command (forward|back|left|right), distance_cm, angle_deg, speed
            cmd = mv.get("command")
            distance = mv.get("distance_cm")
            angle = mv.get("angle_deg")
            mv_speed = mv.get("speed")
            if cmd in ("forward", "back") and distance is not None:
                # Format: MOVE|direction|distance_cm|speed
                move_cmd = f"MOVE|{cmd}|{int(distance)}|{int(mv_speed) if mv_speed else int(speed)}"
            elif cmd in ("left", "right") and angle is not None:
                # Format: TURN|direction|angle_deg|speed
                move_cmd = f"TURN|{cmd}|{int(angle)}|{int(mv_speed) if mv_speed else int(speed)}"
            elif cmd == "stop":
                move_cmd = "STOP"
    except Exception as e:
        print("Warning handling move:", e)

    return move_cmd


# expose agi_loop to the MCU
Bridge.provide("agi_loop", agi_loop)
