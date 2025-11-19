from arduino.app_utils import *
import os
import time
import cv2
import speech_recognition as sr
import pyttsx3
import google.generativeai as genai
import threading
import re

# Configuration
CAMERA_INDEX = 0
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Global state for Bridge communication
next_command = "NOOP"
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
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.chat = self.model.start_chat(history=[])
        
        self.system_prompt = """
        You are a robot assistant.
        To move a servo, include [SERVO: <index>, <angle>].
        Servo 0: Head, 1: Left Arm, 2: Right Arm.
        Keep responses concise.
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
        # Extract commands
        commands = re.findall(r'\[SERVO:\s*(\d+),\s*(\d+)\]', response_text)
        for index, angle in commands:
            # Format: S<index>:<angle>
            cmd = f"S{index}:{angle}"
            self.queue_command(cmd)
            # Note: This simple queue only holds the LAST command. 
            # For multiple, we'd need a list and pop them.
            # For now, let's just send the last one or join them.
            
        clean_text = re.sub(r'\[SERVO:.*?\]', '', response_text)
        return clean_text

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
                    
                    response = self.chat.send_message(inputs)
                    clean_text = self.process_response(response.text)
                    self.speak(clean_text)
                except Exception as e:
                    print(f"Error: {e}")

# Bridge Function called by Arduino
def tick():
    global next_command
    with command_lock:
        cmd = next_command
        next_command = "NOOP"
    return cmd

if __name__ == "__main__":
    # Start Brain in background thread
    brain = RobotBrain()
    t = threading.Thread(target=brain.run_loop)
    t.daemon = True
    t.start()

    # Register Bridge functions
    Bridge.provide("tick", tick)
    
    # Run Bridge App (handles Serial comms)
    print("Starting Bridge App...")
    App.run()
