import os
import time
import cv2
import serial
import serial.tools.list_ports
import speech_recognition as sr
import pyttsx3
import google.generativeai as genai
from threading import Thread

# Configuration
SERIAL_PORT = "COM3" # Update this to your Arduino's port
BAUD_RATE = 115200
CAMERA_INDEX = 0
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") # Set this env var

class RobotBody:
    def __init__(self, port=SERIAL_PORT, baud=BAUD_RATE):
        self.ser = None
        try:
            self.ser = serial.Serial(port, baud, timeout=1)
            time.sleep(2) # Wait for Arduino to reset
            print(f"Connected to Robot Body on {port}")
        except Exception as e:
            print(f"Could not connect to Robot Body: {e}")
            print("Running in simulation mode (no movement).")

    def move_servo(self, index, angle):
        if self.ser:
            command = f"S{index}:{angle}\n"
            self.ser.write(command.encode())
            print(f"Sent: {command.strip()}")
        else:
            print(f"[SIM] Moving Servo {index} to {angle}")

class RobotBrain:
    def __init__(self, body):
        self.body = body
        self.setup_audio()
        self.setup_camera()
        self.setup_ai()

    def setup_audio(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.engine = pyttsx3.init()
        # Configure voice if needed
        voices = self.engine.getProperty('voices')
        if voices:
            self.engine.setProperty('voice', voices[0].id) 

    def setup_camera(self):
        self.cap = cv2.VideoCapture(CAMERA_INDEX)
        if not self.cap.isOpened():
            print("Warning: Could not open camera.")

    def setup_ai(self):
        if not GEMINI_API_KEY:
            print("Warning: GEMINI_API_KEY not found. AI features will not work.")
            return
        
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.chat = self.model.start_chat(history=[])
        
        # System prompt to guide behavior
        self.system_prompt = """
        You are a robot assistant. You can see and hear.
        You can control your servos.
        To move a servo, include a command in your response like [SERVO: <index>, <angle>].
        Example: "Hello! I am waving. [SERVO: 0, 45] [SERVO: 0, 135]"
        Servo 0 is the head (0-180).
        Servo 1 is the left arm.
        Servo 2 is the right arm.
        Keep responses concise and conversational.
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
            except sr.WaitTimeoutError:
                return None
            except sr.UnknownValueError:
                return None
            except sr.RequestError as e:
                print(f"Could not request results; {e}")
                return None

    def see(self):
        if not self.cap.isOpened():
            return None
        ret, frame = self.cap.read()
        if ret:
            # Convert to RGB for Gemini
            return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return None

    def process_commands(self, response_text):
        # Simple parsing for [SERVO: i, a]
        import re
        commands = re.findall(r'\[SERVO:\s*(\d+),\s*(\d+)\]', response_text)
        for index, angle in commands:
            self.body.move_servo(int(index), int(angle))
        
        # Remove commands from spoken text
        clean_text = re.sub(r'\[SERVO:.*?\]', '', response_text)
        return clean_text

    def run(self):
        self.speak("System online. Waiting for input.")
        
        while True:
            user_input = self.listen()
            
            if user_input:
                if "exit" in user_input.lower() or "quit" in user_input.lower():
                    self.speak("Shutting down.")
                    break
                
                image = self.see()
                
                try:
                    inputs = [user_input]
                    if image is not None:
                        from PIL import Image
                        pil_img = Image.fromarray(image)
                        inputs.append(pil_img)
                    
                    response = self.chat.send_message(inputs)
                    response_text = response.text
                    
                    clean_text = self.process_commands(response_text)
                    self.speak(clean_text)
                    
                except Exception as e:
                    print(f"AI Error: {e}")
                    self.speak("I had trouble thinking about that.")

        if self.cap.isOpened():
            self.cap.release()

if __name__ == "__main__":
    # List available ports
    ports = list(serial.tools.list_ports.comports())
    print("Available ports:")
    for p in ports:
        print(f"- {p.device}")

    body = RobotBody() # Will use default port or fail gracefully
    brain = RobotBrain(body)
    brain.run()
