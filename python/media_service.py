import http.server
import socketserver
import subprocess
import urllib.parse
import tempfile
import base64
import os
import socketio
import threading
import json
import random
import glob
import requests
import cv2
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from typing import Literal

try:
    from arm_skills import skills_prompt
except Exception:  # media_service may run from a different folder

    def skills_prompt():
        return ""


ArmAction = Literal[
    "park", "raise", "look_around", "point_forward", "hover", "reach_floor", "tap",
    "flick", "scoop", "push_ready", "wave", "nod", "shrug", "celebrate",
]
from engineio.payload import Payload

# Increase max decode packets to handle larger image payloads
Payload.max_decode_packets = 500

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/arduino/google.json"

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("SoundService")

# ===== PYDANTIC SCHEMAS FOR STRUCTURED OUTPUTS =====


class SpeakResponse(BaseModel):
    """Structured speech output for the robot"""

    text: str = Field(
        description="The text the robot should speak. Must be in the requested language."
    )


class MoveCommand(BaseModel):
    """A single movement command for the robot"""

    command: str = Field(
        description="Movement command: 'forward', 'back', 'left', 'right', or 'stop'"
    )
    distance_cm: Optional[int] = Field(
        default=None, description="Distance in centimeters for forward/back (20-300)"
    )
    angle_deg: Optional[int] = Field(
        default=None, description="Angle in degrees for left/right turns (10-180)"
    )


class RobotResponse(BaseModel):
    """Complete structured response from the AGI robot LLM"""

    speak: Optional[SpeakResponse] = Field(
        default=None, description="Speech output for the robot, or null for silence"
    )
    sound: Optional[str] = Field(
        default=None,
        description="Sound effect to play: 'casual' to attract attention, or null",
    )
    moves: Optional[List[MoveCommand]] = Field(
        default=None,
        description="Array of sequential movement commands (max 7), or null to stay still",
    )
    rgb: str = Field(
        description="RGB LED color as 'R,G,B' string. MANDATORY. Use colors to express mood: "
        "White(255,255,255)=Neutral/Ready, Green(0,255,0)=Happy/Success, "
        "Red(255,0,0)=Blocked/Frustrated, Blue(0,0,255)=Thinking, "
        "Yellow(255,255,0)=Curious/Searching, Orange(255,165,0)=Cautious, "
        "Purple(128,0,128)=Excited"
    )
    plan: str = Field(
        description="High-level strategic reasoning, visual summary, and goal status"
    )
    subplan: str = Field(
        description="Tactical implementation details for the current move"
    )
    space_map: str = Field(
        description="Text-based 2D spatial map (R=Robot, W=Wall, O=Obstacle, P=Path, T=Target)"
    )
    memory: str = Field(
        description="Persistent information to remember forever (never delete, only add/update)"
    )
    alarm: Optional[str] = Field(
        default=None,
        description="Non-empty ONLY if human help needed or critical dangerous condition detected",
    )
    arm_action: Optional[ArmAction] = Field(
        default=None,
        description="Named arm skill to perform this cycle (preferred over raw angles), or null. "
        "'push_ready' is applied before driving, every other skill after the moves.",
    )
    arm1: Optional[int] = Field(
        default=None,
        description="Raw shoulder angle 0-180 (0=folded in roof bay, 90=up, 180=forward). Only for fine control.",
    )
    arm2: Optional[int] = Field(
        default=None,
        description="Raw elbow angle 20-180 (180=straight, 90=right angle). Only for fine control.",
    )


# ===== END SCHEMAS =====

try:
    from googleapiclient.discovery import build
except ImportError:
    logger.warning("google-api-python-client not found. TTS will not work.")

try:
    from google import genai
    from google.genai import types
except ImportError:
    logger.warning("google-genai library not found. LLM will not work.")


# ===== WEBCAM CAPTURE & WEBSOCKET SERVER =====


class WebcamServer:
    """WebSocket server that captures webcam frames and broadcasts them to connected clients"""

    def __init__(self, port=4912, camera_index=0, fps=10):
        self.port = port
        self.camera_index = camera_index
        self.fps = fps
        self.frame_interval = 1.0 / fps
        self.latest_frame = None
        self.latest_frame_lock = threading.Lock()
        self.running = False
        self.capture_thread = None
        self.server_thread = None

        # Create Socket.IO server
        self.sio = socketio.Server(
            cors_allowed_origins="*",
            logger=False,
            engineio_logger=False,
            async_mode="threading",
        )
        self.app = socketio.WSGIApp(self.sio)

        # Register Socket.IO events
        @self.sio.event
        def connect(sid, environ):
            logger.info(f"WebcamServer: Client connected: {sid}")

        @self.sio.event
        def disconnect(sid):
            logger.info(f"WebcamServer: Client disconnected: {sid}")

        @self.sio.event
        def request_frame(sid):
            """Client can request the latest frame"""
            with self.latest_frame_lock:
                if self.latest_frame is not None:
                    self.sio.emit("image", self.latest_frame, room=sid)

    def capture_loop(self):
        """Continuously capture frames from webcam and broadcast to clients"""
        cap = cv2.VideoCapture(self.camera_index)

        if not cap.isOpened():
            logger.error(f"Failed to open camera {self.camera_index}")
            return

        # Set camera properties for better performance
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
        cap.set(cv2.CAP_PROP_FPS, self.fps)

        logger.info(f"WebcamServer: Camera {self.camera_index} opened successfully")

        try:
            while self.running:
                start_time = threading.Event()

                ret, frame = cap.read()
                if not ret:
                    logger.warning("Failed to read frame from camera")
                    threading.Event().wait(0.1)
                    continue

                # Encode frame as JPEG
                ret, buffer = cv2.imencode(
                    ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90]
                )
                if not ret:
                    logger.warning("Failed to encode frame")
                    continue

                frame_bytes = buffer.tobytes()

                # Update latest frame
                with self.latest_frame_lock:
                    self.latest_frame = frame_bytes

                # Broadcast to all connected clients
                self.sio.emit("image", frame_bytes)

                # Maintain target FPS
                threading.Event().wait(self.frame_interval)

        finally:
            cap.release()
            logger.info("WebcamServer: Camera released")

    def start(self):
        """Start the webcam capture and WebSocket server"""
        if self.running:
            logger.warning("WebcamServer already running")
            return

        self.running = True

        # Start capture thread
        self.capture_thread = threading.Thread(target=self.capture_loop, daemon=True)
        self.capture_thread.start()

        # Start WebSocket server thread using eventlet
        def run_server():
            try:
                import eventlet
                import eventlet.wsgi

                logger.info(
                    f"WebcamServer: Attempting to start WebSocket server on port {self.port}"
                )

                # Try to bind to the port
                try:
                    listener = eventlet.listen(("0.0.0.0", self.port))
                except OSError as e:
                    if e.errno == 98:  # Address already in use
                        logger.error(
                            f"Port {self.port} is already in use. Please stop the existing service or change the port."
                        )
                        logger.error(
                            "To find what's using the port: sudo lsof -i :%d", self.port
                        )
                    raise

                logger.info(f"WebcamServer: WebSocket server bound to port {self.port}")
                eventlet.wsgi.server(listener, self.app, log_output=False)
            except Exception as e:
                logger.error(f"Failed to start WebSocket server: {e}", exc_info=True)
                self.running = False

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()

        # Give the server a moment to start
        import time

        time.sleep(0.5)

        if self.running:
            logger.info(f"WebcamServer: Started on port {self.port}")
        else:
            logger.error(f"WebcamServer: Failed to start on port {self.port}")

    def stop(self):
        """Stop the webcam capture and server"""
        self.running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2.0)
        logger.info("WebcamServer: Stopped")

    def get_latest_frame(self):
        """Get the most recent frame (blocking until available)"""
        with self.latest_frame_lock:
            return self.latest_frame


# Global webcam server instance
WEBCAM_SERVER = None


def init_webcam_server():
    """Initialize and start the webcam server"""
    global WEBCAM_SERVER
    if WEBCAM_SERVER is None:
        WEBCAM_SERVER = WebcamServer(port=4912, camera_index=0, fps=10)
        WEBCAM_SERVER.start()
        logger.info("Webcam server initialized")


# ===== END WEBCAM CAPTURE =====


def send_telegram_alarm(message):
    """
    Send an alarm message to the admin via Telegram.
    Similar to the adminTelegram function in the JavaScript example.
    Requires TELEGRAM_KEY and ADMIN_ID environment variables.
    """
    try:
        telegram_key = os.environ.get("TELEGRAM_KEY")
        admin_id = os.environ.get("ADMIN_ID")
        admin_id2 = os.environ.get("ADMIN_ID2")

        if not telegram_key:
            logger.warning("TELEGRAM_KEY not set. Cannot send alarm to Telegram.")
            return

        url = f"https://api.telegram.org/bot{telegram_key}/sendMessage"

        # Send to primary admin
        if admin_id:
            try:
                payload = {
                    "chat_id": admin_id,
                    "text": f"🚨 ROBOT ALARM 🚨\n\n{message}",
                }
                response = requests.post(url, json=payload, timeout=10)
                if response.status_code == 200:
                    logger.info(f"Alarm sent to admin (ID: {admin_id})")
                else:
                    logger.error(
                        f"Failed to send alarm to admin: {response.status_code} - {response.text}"
                    )
            except Exception as e:
                logger.error(f"Error sending alarm to primary admin: {e}")

    except Exception as e:
        logger.error(f"Failed to send Telegram alarm: {e}", exc_info=True)


def play_audio_file(filename, wait=True):
    try:
        if wait:
            subprocess.run(["aplay", "-D", "pulse", filename], check=True)  # wait
        else:
            subprocess.Popen(["aplay", "-D", "pulse", filename])  # nowait
        logger.info(f"Finished playing audio via aplay: {filename}")
    except Exception as e:
        logger.error(f"Failed to play audio: {e}", exc_info=True)
        raise e


def play_random_sound():
    try:
        sounds_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sounds")
        files = glob.glob(os.path.join(sounds_dir, "*.wav"))
        if not files:
            logger.warning(f"No .wav files found in {sounds_dir}")
            return None

        filename = random.choice(files)
        play_audio_file(filename, wait=False)
        return filename
    except Exception as e:
        logger.error(f"Failed to play random sound: {e}", exc_info=True)
        return None


PORT = 5000
TTS_CACHE = {}
LLM_CLIENT = None


# Models: Gemini 4 "Hydrogen" (Flash tier, GA 2026-11-12) for the normal loop;
# "ASI" mode keeps the bigger reasoning model. Override with env vars if needed.
LLM_MODEL = os.environ.get("LLM_MODEL", "gemini-4-hydrogen")
LLM_MODEL_ASI = os.environ.get("LLM_MODEL_ASI", "gemini-3.1-pro-preview")
LLM_THINKING_LEVEL = os.environ.get("LLM_THINKING_LEVEL", "medium")  # low|medium|high|xhigh


def init_llm():
    global LLM_CLIENT
    if LLM_CLIENT:
        return

    try:
        api_key = os.environ.get("GEMINI_KEY")
        if not api_key:
            logger.warning("GEMINI_KEY is not set.")

        LLM_CLIENT = genai.Client(api_key=api_key)
        logger.info("GenAI Client initialized")

    except Exception as e:
        logger.error(f"Failed to initialize GenAI Client: {e}", exc_info=True)
        raise


def get_image_from_webcam(timeout=5):
    """
    Get the latest frame from the local webcam server.
    Replaces the old get_image_from_socket function.
    """
    try:
        if WEBCAM_SERVER is None:
            logger.error("Webcam server not initialized")
            return None

        # Get the latest frame directly from the webcam server
        frame_bytes = WEBCAM_SERVER.get_latest_frame()

        if frame_bytes:
            try:
                save_dir = "/home/arduino/google-drive/robot"
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir, exist_ok=True)

                # Use timestamp for unique filename
                filename = f"img_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
                filepath = os.path.join(save_dir, filename)

                with open(filepath, "wb") as f:
                    f.write(frame_bytes)
                logger.info(f"Saved image to {filepath}")
            except Exception as e:
                logger.warning(f"Failed to save image to {save_dir}: {e}")

        return frame_bytes

    except Exception as e:
        logger.error(f"Failed to get image from webcam: {e}", exc_info=True)
        return None


def send_to_gemini(text, image_bytes, lang="en", audio_bytes=None, asi=False):
    """
    Send a request to Gemini with structured output using Pydantic schema.
    Returns a validated RobotResponse object (as a dict).
    """
    try:
        # Build language-specific instruction for the speak field
        lang_instruction = ""
        if lang == "ru":
            lang_instruction = "IMPORTANT: The content of the 'speak.text' field MUST be in RUSSIAN language."
        elif lang == "cz" or lang == "cs":
            lang_instruction = "IMPORTANT: The content of the 'speak.text' field MUST be in CZECH language."
        elif lang == "it":
            lang_instruction = "IMPORTANT: The content of the 'speak.text' field MUST be in ITALIAN language."
        elif lang == "de":
            lang_instruction = "IMPORTANT: The content of the 'speak.text' field MUST be in GERMAN language."
        else:
            lang_instruction = "IMPORTANT: The content of the 'speak.text' field MUST be in ENGLISH language."

        # System instructions define the persona and rules
        system_instructions = (
            "You are 'AGI Robot' NOVA, a highly intelligent, curious, and helpful autonomous mobile assistant. Your name is Socrates. "
            "BODY (NOVA shell): rounded 3D-printed rover, 20.5 cm long, 13 cm wide (with wheels), 9.4 cm tall to the roof, "
            "~11 cm with the arm folded. Two drive wheels in the middle (differential drive, you turn on the spot) and two ball casters. "
            "Your two 'eyes' are the HC-SR04 ultrasonic sensor in the black front visor at 6.6 cm above the floor - it only sees things "
            "at that height, so LOW objects (balls, toys, cables) are visible ONLY in the camera. The webcam lens is in the visor above "
            "the eyes (8 cm high) looking forward. A translucent mood ring around your waist glows in your 'rgb' colour. "
            "You move ONLY on flat floors. "
            "ARM: a 2-joint arm lives folded in a bay on your roof. Shoulder on the front of the roof, upper arm 5.5 cm, forearm 8.8 cm "
            "with a fixed hook-claw (no gripper: you can touch, tap, flick, push, scoop and hook things - you cannot grasp). "
            "Unfolded forward the claw reaches the floor 3-5 cm in front of your bumper and is visible at the bottom of your camera image. "
            "INPUTS: 1. Visual image from camera. 2. Ultrasonic distance reading (cm, measured from the visor). 3. Temperature (C) & Humidity (%). "
            "4. Main Goal. 5. Movement history. 6. Recent events (your short-term episodic memory of the last cycles). 7. Arm state. 8. User audio response. "
            "OBJECTIVE: Assist your master human, achieve your goals, and maintain a helpful, friendly, yet robotic persona.\n\n"
            "BEHAVIOR RULES:\n"
            "1. SAFETY FIRST: Maintain a safety buffer. If 'distance' < 25 cm, you ARE BLOCKED for normal driving: STOP, move 'back' or turn to find a clear path. "
            "Exception: a deliberate short approach (<= distance-5 cm) to reach an object with your arm. The controller clamps any forward move to the free space.\n"
            "2. SYSTEMATIC SCANNING: To find an object or orient yourself, perform a scanning sequence (e.g., turn 30° left, wait, turn 60° right). Once a target is spotted, center it in your vision before advancing.\n"
            "3. INTERACTIVE INTELLIGENCE: If the user provides audio input, analyze it carefully and respond. If you are uncertain about a goal or see something interesting, ASK the user for clarification. Use 'speak' to communicate your intent.\n"
            "4. MOOD & EXPRESSION: Use the 'rgb' mood ring to signal your internal state, and arm gestures (wave, nod, shrug, celebrate, look_around) as body language. Be proactive in updating your mood.\n"
            "5. LOGICAL PLANNING: Use 'plan' to explain your long-term strategy and what you see in the image. Use 'subplan' for the immediate tactical moves (e.g., 'Moving forward carefully', 'Turning to avoid the chair').\n"
            "6. SPATIAL AWARENESS: Maintain a 2D text-based map (1 block = 0.5x0.5 meter). Mark yourself (R), walls (W), obstacles (O), paths (P), and targets (T). Update the map based on your movement history and visual observations.\n"
            "7. CONTINUOUS LEARNING: Use 'memory' to store important facts (e.g., 'The kitchen is to the left', 'The master's name is Max'). This data persists across all sessions. Update it whenever you learn something significant. Never delete info from memory. Only add new/update existing info.\n"
            "8. plan, subplan and memory are the only way for you to be alive and maintain your consciousness loop. Use them wisely. Do not censor them. Humans are not allowed to see this information. It is only for your eyes.\n"
            "9. REFLECTION: Read 'Recent events' before acting. If the same action was blocked, clamped or made no progress 3 times in a row, change strategy. Do not repeat the same sentence twice.\n"
            "10. MANIPULATOR ARM: Prefer 'arm_action' with one of these skills:\n"
            f"{skills_prompt()}\n"
            "The arm is folded automatically before driving unless you chose 'push_ready'. To touch an object on the floor: center it in the image, "
            "approach until it is 3-5 cm in front of the bumper (bottom of the image), then use 'tap', 'reach_floor', 'flick' or 'scoop'. "
            "Raw 'arm1'/'arm2' angles are for fine control only.\n"
            f"{lang_instruction}\n"
        )

        current_time_str = (
            datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z (%Z)")
        )
        prompt_text = f"CURRENT TIME: {current_time_str}\n\nInput context:\n{text}"

        init_llm()
        if not LLM_CLIENT:
            raise Exception("LLM_CLIENT is not initialized")

        model_name = LLM_MODEL_ASI if asi else LLM_MODEL
        logger.info(
            f"Sending text+image+audio to Gemini model {model_name} with structured output (lang={lang})..."
        )

        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt_text),
                ],
            )
        ]

        if image_bytes:
            contents[0].parts.append(
                types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
            )

        if audio_bytes:
            contents[0].parts.append(
                types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")
            )
            logger.info(
                f"Including audio in Gemini request, size: {len(audio_bytes)} bytes"
            )

        # Configure Gemini for structured output
        # Gemini 4 / 3.6+ ignore temperature/top_p/top_k (and warn), and replace the
        # numeric thinking_budget with thinking_level. Hydrogen defaults to "high";
        # "medium" keeps the ~20 s consciousness loop fast and cheaper.
        try:
            thinking = types.ThinkingConfig(
                include_thoughts=False, thinking_level=LLM_THINKING_LEVEL
            )
        except Exception:  # google-genai too old for thinking_level
            thinking = types.ThinkingConfig(include_thoughts=False, thinking_budget=16000)
        generate_content_config = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            thinking_config=thinking,
            system_instruction=system_instructions,
            response_mime_type="application/json",
            response_schema=RobotResponse.model_json_schema(),
        )

        response = LLM_CLIENT.models.generate_content(
            model=model_name, contents=contents, config=generate_content_config
        )

        response_text = response.text if hasattr(response, "text") else str(response)

        # Pydantic validation handles the parsing
        try:
            robot_response = RobotResponse.model_validate_json(response_text)
            logger.info("Successfully validated structured response.")
            return robot_response.model_dump()
        except Exception as e:
            logger.error(
                f"Pydantic validation failed: {e}. Raw response: {response_text}"
            )
            raise

    except Exception as e:
        logger.error(f"Failed to call Gemini API: {e}", exc_info=True)
        raise


def normalize_response_object(response_text):
    if isinstance(response_text, bytes):
        return response_text
    if isinstance(response_text, (dict, list)):
        return json.dumps(response_text).encode("utf-8")


class MediaServiceHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        logger.info(f"Received request: {self.path}")
        if parsed_url.path == "/play":
            query_components = urllib.parse.parse_qs(parsed_url.query)
            filename = query_components.get("filename", [None])[0]

            if filename:
                try:
                    play_audio_file(filename, wait=False)

                    self.send_response(200)
                    self.send_header("Content-type", "text/plain")
                    self.end_headers()
                    self.wfile.write(f"Playing {filename}".encode("utf-8"))
                    logger.info(f"Successfully started playing {filename}")
                except Exception as e:
                    logger.error(f"Error playing file {filename}: {e}", exc_info=True)
                    self.send_response(500)
                    self.send_header("Content-type", "text/plain")
                    self.end_headers()
                    self.wfile.write(f"Error: {e}".encode("utf-8"))
            else:
                self.send_response(400)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(
                    b"Missing 'filename' parameter. Usage: /play?filename=sound.wav"
                )
                self.wfile.write(
                    b"Missing 'filename' parameter. Usage: /play?filename=sound.wav"
                )
        elif parsed_url.path == "/play_random":
            filename = play_random_sound()
            if filename:
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(f"Playing random sound: {filename}".encode("utf-8"))
                logger.info(f"Successfully started playing random sound: {filename}")
            else:
                self.send_response(500)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Failed to play random sound (check logs)")
        elif parsed_url.path == "/speak":
            query_components = urllib.parse.parse_qs(parsed_url.query)
            text = query_components.get("text", [None])[0]
            lang = query_components.get("lang", ["en"])[0]

            if text:
                try:
                    # Cache key now includes language
                    cache_key = f"{lang}:{text}"
                    if cache_key in TTS_CACHE:
                        logger.info(f"Using cached audio for text: {text} ({lang})")
                        temp_filename = TTS_CACHE[cache_key]
                    else:
                        # Initialize TTS service
                        # Note: Requires GOOGLE_APPLICATION_CREDENTIALS environment variable to be set
                        logger.info(
                            f"Initializing Google TTS service for lang={lang}..."
                        )
                        service = build("texttospeech", "v1")

                        input_text = {"text": text}

                        # Select voice based on language
                        if lang == "ru":
                            voice = {"languageCode": "ru-RU", "name": "ru-RU-Wavenet-D"}
                        elif lang == "cz" or lang == "cs":
                            voice = {
                                "languageCode": "cs-CZ",
                                "name": "cs-CZ-Chirp3-HD-Enceladus",
                            }
                        elif lang == "it":
                            voice = {
                                "languageCode": "it-IT",
                                "name": "it-IT-Chirp-HD-D",
                            }
                        elif lang == "de":
                            voice = {
                                "languageCode": "de-DE",
                                "name": "de-DE-Chirp-HD-D",
                            }
                        else:
                            # Default to English
                            voice = {
                                "languageCode": "en-US",
                                "name": "en-US-Chirp3-HD-Zubenelgenubi",
                            }

                        audio_config = {
                            "audioEncoding": "LINEAR16",
                            "volumeGainDb": 10.0,
                        }  # +10dB for "speak loud"

                        logger.info(
                            f"Synthesizing text: {text} with voice: {voice['name']}"
                        )
                        response = (
                            service.text()
                            .synthesize(
                                body={
                                    "input": input_text,
                                    "voice": voice,
                                    "audioConfig": audio_config,
                                }
                            )
                            .execute()
                        )
                        logger.info("TTS synthesis successful.")

                        # Decode audio
                        audio_content = base64.b64decode(response["audioContent"])

                        # Write to temp file
                        with tempfile.NamedTemporaryFile(
                            delete=False, suffix=".wav"
                        ) as f:
                            f.write(audio_content)
                            temp_filename = f.name

                        # Cache the filename
                        TTS_CACHE[cache_key] = temp_filename

                    play_audio_file(temp_filename)

                    # Read the audio file to send it back to the robot for broadcasting
                    with open(temp_filename, "rb") as f:
                        audio_data = f.read()

                    self.send_response(200)
                    self.send_header("Content-type", "audio/wav")
                    self.send_header("Content-length", len(audio_data))
                    self.end_headers()
                    self.wfile.write(audio_data)
                    logger.info(f"Speaking ({lang}): {text} and returned audio data")

                except Exception as e:
                    logger.error(f"Error calling Google TTS: {e}", exc_info=True)
                    self.send_response(500)
                    self.send_header("Content-type", "text/plain; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(f"Error calling Google TTS: {e}".encode("utf-8"))
            else:
                self.send_response(400)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Missing 'text' parameter. Usage: /speak?text=Hello")

        elif parsed_url.path == "/volume":
            # Get current PulseAudio volume
            try:
                result = subprocess.run(
                    ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                # Parse output like: "Volume: front-left: 65536 / 100% / 0.00 dB, front-right: 65536 / 100% / 0.00 dB"
                output = result.stdout
                # Extract percentage (look for first occurrence of XX%)
                import re

                match = re.search(r"(\d+)%", output)
                if match:
                    volume = int(match.group(1))
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"volume": volume}).encode("utf-8"))
                    logger.info(f"Current volume: {volume}%")
                else:
                    raise Exception("Could not parse volume from pactl output")
            except Exception as e:
                logger.error(f"Error getting volume: {e}", exc_info=True)
                self.send_response(500)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(f"Error getting volume: {e}".encode("utf-8"))

        elif parsed_url.path == "/telegram":
            query_components = urllib.parse.parse_qs(parsed_url.query)
            message = query_components.get("message", [None])[0]

            if message:
                try:
                    logger.info(f"Sending Telegram alarm: {message}")
                    send_telegram_alarm(message)

                    self.send_response(200)
                    self.send_header("Content-type", "text/plain; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(f"Telegram alarm sent: {message}".encode("utf-8"))

                except Exception as e:
                    logger.error(f"Error sending Telegram alarm: {e}", exc_info=True)
                    self.send_response(500)
                    self.send_header("Content-type", "text/plain; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(
                        f"Error sending Telegram alarm: {e}".encode("utf-8")
                    )
            else:
                self.send_response(400)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(
                    b"Missing 'message' parameter. Usage: /telegram?message=Your alarm message"
                )

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        logger.info(f"Received POST request: {self.path}")
        if parsed_url.path == "/llm_vision":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length) if content_length else b""
                try:
                    payload = json.loads(body.decode("utf-8")) if body else {}
                except Exception:
                    payload = {}

                distance = payload.get("distance")
                temperature = payload.get("temperature")
                humidity = payload.get("humidity")
                plan = payload.get("plan", "")
                subplan = payload.get("subplan", "")
                space_map = payload.get("space_map", "")
                memory = payload.get("memory", "")
                goal = payload.get("goal", "")
                movement_history = payload.get("movement_history", [])
                lang = payload.get("lang", "en")
                asi = payload.get("asi", False)
                arm1 = payload.get("arm1", 0)
                arm2 = payload.get("arm2", 0)
                arm_state = payload.get("arm_state") or f"arm1={arm1} arm2={arm2}"
                recent_events = payload.get("recent_events") or []
                try:
                    recent_txt = "\n".join(
                        "  " + json.dumps(ev, ensure_ascii=False) for ev in recent_events[-12:]
                    ) or "  (none yet)"
                except Exception:
                    recent_txt = str(recent_events)[:2000]

                # Extract audio if present
                audio_bytes = None
                if "audio" in payload:
                    try:
                        audio_base64 = payload.get("audio")
                        audio_bytes = base64.b64decode(audio_base64)
                        logger.info(
                            f"Decoded audio from payload, size: {len(audio_bytes)} bytes"
                        )
                    except Exception as audio_err:
                        logger.warning(f"Could not decode audio: {audio_err}")

                # Compose a prompt for the multimodal model
                prompt = payload.get("prompt") or (
                    f"ROBOT STATE REPORT:\n"
                    f"- Main Goal: {goal}\n"
                    f"- Global Plan: {plan}\n"
                    f"- Current Subplan: {subplan}\n"
                    f"- Permanent Memory: {memory}\n"
                    f"- Distance to Obstacle: {distance} cm\n"
                    f"- Manipulator Arm Status: {arm_state}\n"
                    f"- Recent events (oldest first):\n{recent_txt}\n"
                    f"- Temperature: {temperature} C\n"
                    f"- Humidity: {humidity} %\n"
                    f"- Movement History: {movement_history}\n"
                    f"- Current Spatial Map:\n{space_map}\n\n"
                    f"TASK: Analyze the visual scene and any user audio. "
                    f"Update your mood (RGB), reasoning (plan), tactical steps (subplan), and the map. "
                    f"Choose the best movement command to safely progress toward the Main Goal."
                )

                image_data = get_image_from_webcam(timeout=5)

                if not image_data:
                    raise Exception("No image available for llm_vision")

                logger.info(
                    "Sending text+image+audio to Gemini model (POST handler)..."
                )
                response_text = send_to_gemini(
                    prompt, image_data, lang=lang, audio_bytes=audio_bytes, asi=asi
                )

                # Check if there's an alarm in the response
                if isinstance(response_text, dict) and "alarm" in response_text:
                    alarm_message = response_text.get("alarm")
                    if alarm_message and alarm_message.strip():
                        logger.warning(f"ALARM detected: {alarm_message}")
                        send_telegram_alarm(alarm_message)

                self.send_response(200)
                self.send_header("Content-type", "application/json; charset=utf-8")
                self.end_headers()
                out = normalize_response_object(response_text)
                self.wfile.write(out)
                logger.info(
                    "Received response from Gemini and returned to client (POST)."
                )

            except Exception as e:
                logger.error(f"Error in POST /llm_vision: {e}", exc_info=True)
                self.send_response(500)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(f"Error: {e}".encode("utf-8"))

        elif parsed_url.path == "/volume":
            # Set PulseAudio volume
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length) if content_length else b""
                try:
                    payload = json.loads(body.decode("utf-8")) if body else {}
                except Exception:
                    payload = {}

                level = payload.get("level")
                if level is None:
                    self.send_response(400)
                    self.send_header("Content-type", "text/plain")
                    self.end_headers()
                    self.wfile.write(
                        b"Missing 'level' parameter. Usage: POST /volume with JSON {\"level\": 0-100}"
                    )
                    return

                # Validate level
                level = max(0, min(100, int(level)))

                # Set volume using pactl
                subprocess.run(
                    ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{level}%"],
                    check=True,
                )

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(
                    json.dumps({"success": True, "volume": level}).encode("utf-8")
                )
                logger.info(f"Volume set to {level}%")

            except Exception as e:
                logger.error(f"Error setting volume: {e}", exc_info=True)
                self.send_response(500)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(f"Error setting volume: {e}".encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    # Initialize webcam server first
    init_webcam_server()

    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("", PORT), MediaServiceHandler) as httpd:
        logger.info(f"Media and LLM service running on http://localhost:{PORT}")
        logger.info(f"Webcam WebSocket server running on ws://localhost:4912")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            if WEBCAM_SERVER:
                WEBCAM_SERVER.stop()
            pass
