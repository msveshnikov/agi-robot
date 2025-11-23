from arduino.app_utils import *
import os
import time
import cv2
import speech_recognition as sr
import pyttsx3
import google.generativeai as genai
import threading
import re
import json

# Configuration
CAMERA_INDEX = 0
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Global state for Bridge communication
next_command = "NOOP"
sensor_data = {"distance": 0} # Placeholder for sensor data
command_lock = threading.Lock()

class RobotBrain:
    def __init__(self):
        self.setup_audio()
        self.setup_camera()
        self.setup_ai()
        self.running = True

    def setup_audio(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.engine = pyttsx3.init()
        self.engine.setProperty('volume', 1.0) # Speak loudly
        voices = self.engine.getProperty('voices')
        if voices:
            self.engine.setProperty('voice', voices[0].id) 

    def setup_camera(self):
        self.cap = cv2.VideoCapture(CAMERA_INDEX)

    def setup_ai(self):
        if not GEMINI_API_KEY:
            print("Warning: GEMINI_API_KEY not found.")
            return
        
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-robotics-er-1.5-preview')
        self.chat = self.model.start_chat(history=[])
        
        self.system_prompt = """
        You are a robot assistant with two wheels (differential drive) and NO arms or head.
        You have an LED matrix for a face and two extra LEDs for eyes.
        You must respond in valid JSON format ONLY.
        The JSON schema is:
        {
            "speech": "text to speak",
            "left_motor": int (speed -100 to 100),
            "right_motor": int (speed -100 to 100),
            "emotion": "neutral" | "happy" | "sad" | "angry" | "surprised",
            "eyes": {"left": bool, "right": bool}
        }
        Positive motor values move forward, negative backward.
        """
        self.chat.send_message(self.system_prompt)

    def speak(self, text):
        print(f"Robot: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def listen(self):
        with self.microphone as source:
            print("Listening...")
            self.recognizer.adjust_for_ambient_noise(source)
            try:
                audio = self.recognizer.listen(source, timeout=5)
                text = self.recognizer.recognize_google(audio)
                print(f"User: {text}")
                return text
            except:
                return None

    def see(self):
        if not self.cap.isOpened():
            return None
        ret, frame = self.cap.read()
        if ret:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return None

    def queue_command(self, cmd):
        global next_command
        with command_lock:
            next_command = cmd

    def process_response(self, response_text):
        try:
            # Clean up potential markdown code blocks
            clean_text = response_text.replace('```json', '').replace('```', '').strip()
            data = json.loads(clean_text)
            
            # Handle speech
            if "speech" in data:
                self.speak(data["speech"])
            
            # Handle motors
            left = data.get("left_motor", 0)
            right = data.get("right_motor", 0)
            
            # Map -100 to 100 speed to servo angles (0-180)
            # 90 is stop. 0 is full reverse (or forward depending on mounting), 180 is full forward.
            # Assuming: 0=Full Back, 90=Stop, 180=Full Fwd
            l_angle = int(90 + (left * 0.9))
            r_angle = int(90 + (right * 0.9)) # Might need to invert one side for differential drive
            
            # Handle Emotion
            emotion_map = {
                "neutral": 0,
                "happy": 1,
                "sad": 2,
                "angry": 3,
                "surprised": 4
            }
            emotion_str = data.get("emotion", "neutral").lower()
            emotion_id = emotion_map.get(emotion_str, 0)
            
            # Handle Eyes
            eyes = data.get("eyes", {"left": False, "right": False})
            l_eye = '1' if eyes.get("left", False) else '0'
            r_eye = '1' if eyes.get("right", False) else '0'
            eyes_cmd = f"{l_eye}{r_eye}"
            
            # Queue commands
            cmd = f"L{l_angle};R{r_angle};E{emotion_id};Y{eyes_cmd}"
            self.queue_command(cmd)
            
        except json.JSONDecodeError:
            print(f"Failed to parse JSON: {response_text}")
            self.speak("I am confused.")

    def run_loop(self):
        self.speak("System online.")
        while self.running:
            user_input = self.listen()
            if user_input:
                if "exit" in user_input.lower():
                    self.speak("Bye.")
                    os._exit(0)
                
                image = self.see()
                try:
                    inputs = [user_input]
                    if image is not None:
                        from PIL import Image
                        pil_img = Image.fromarray(image)
                        inputs.append(pil_img)
                    
                    # Add sensor data context
                    global sensor_data
                    inputs.append(f"Sensor Data: {json.dumps(sensor_data)}")
                    
                    response = self.chat.send_message(inputs)
                    self.process_response(response.text)
                except Exception as e:
                    print(f"Error: {e}")

# Bridge Functions called by Arduino
def tick():
    global next_command
    with command_lock:
        cmd = next_command
        next_command = "NOOP"
    return cmd

def update_sensors(distance):
    global sensor_data
    sensor_data["distance"] = distance
    return True

if __name__ == "__main__":
    # Start Brain in background thread
    brain = RobotBrain()
    t = threading.Thread(target=brain.run_loop)
    t.daemon = True
    t.start()

    # Register Bridge functions
    Bridge.provide("tick", tick)
    Bridge.provide("update_sensors", update_sensors)
    
    # Run Bridge App (handles Serial comms)
    print("Starting Bridge App...")
    App.run()
