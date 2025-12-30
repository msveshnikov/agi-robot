from arduino.app_utils import App
from arduino.app_utils import Bridge
from arduino.app_bricks.web_ui import WebUI
from arduino.app_bricks.video_objectdetection import VideoObjectDetection
from datetime import datetime, UTC
from arduino.app_bricks.arduino_cloud import ArduinoCloud
import urllib.request
import urllib.parse
import os

ui = WebUI()
detection_stream = VideoObjectDetection(confidence=0.5, debounce_sec=0.0)

ui.on_message("override_th", lambda sid, threshold: detection_stream.override_threshold(threshold))

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


arduino_cloud.register("speed", value=0, on_write=speed_callback)
arduino_cloud.register("back", value=False, on_write=back_callback)
arduino_cloud.register("left", value=False, on_write=left_callback)
arduino_cloud.register("right", value=False, on_write=right_callback)
arduino_cloud.register("forward", value=False, on_write=forward_callback)
App.start_brick(arduino_cloud)

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

Bridge.provide("get_speed", get_speed)
Bridge.provide("get_back", get_back)
Bridge.provide("get_left", get_left)
Bridge.provide("get_right", get_right)
Bridge.provide("get_forward", get_forward)

def play_sound(filename):
    try:
        query = urllib.parse.urlencode({'filename': filename})
        url = f"http://172.17.0.1:5000/play?{query}"
        with urllib.request.urlopen(url, timeout=1) as response:
            print(f"Sound service called: {response.read().decode()}")
    except Exception as e:
        print(f"Warning: Could not call sound service: {e}")

Bridge.provide("play_sound", play_sound)

play_sound("/home/arduino/1.wav")

App.run()
