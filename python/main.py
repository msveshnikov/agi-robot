# SPDX-FileCopyrightText: Copyright (C) ARDUINO SRL (http://www.arduino.cc)
#
# SPDX-License-Identifier: MPL-2.0

from arduino.app_utils import App
from arduino.app_bricks.web_ui import WebUI
from arduino.app_bricks.video_objectdetection import VideoObjectDetection
from datetime import datetime, UTC

from arduino.app_bricks.arduino_cloud import ArduinoCloud
from arduino.app_utils import Bridge

ui = WebUI()
detection_stream = VideoObjectDetection(confidence=0.5, debounce_sec=0.0)


ui.on_message("override_th", lambda sid, threshold: detection_stream.override_threshold(threshold))

# Register a callback for when all objects are detected
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

def speed_callback(client: object, value: int):
    global speed
    """Callback function to handle speed updates from cloud."""
    print(f"Speed value updated from cloud: {value}")
    speed = value


arduino_cloud.register("speed", value=0, on_write=speed_callback)
App.start_brick(arduino_cloud)
def get_speed():
    return speed

Bridge.provide("get_speed", get_speed)

App.run()
