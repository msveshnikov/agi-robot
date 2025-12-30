from arduino.app_utils import App
from arduino.app_utils import Bridge
from arduino.app_bricks.web_ui import WebUI
from arduino.app_bricks.video_objectdetection import VideoObjectDetection
from datetime import datetime, UTC
from arduino.app_bricks.arduino_cloud import ArduinoCloud

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

def speed_callback(client: object, value: int):
    global speed
    print(f"Speed value updated from cloud: {value}")
    speed = value

def back_callback(client: object, value: bool):
    global back
    print(f"Speed value updated from cloud: {value}")
    back = value


arduino_cloud.register("speed", value=0, on_write=speed_callback)
arduino_cloud.register("back", value=False, on_write=back_callback)
App.start_brick(arduino_cloud)

def get_speed():
    return speed

def get_back():
    return back

Bridge.provide("get_speed", get_speed)
Bridge.provide("get_back", get_back)

App.run()
