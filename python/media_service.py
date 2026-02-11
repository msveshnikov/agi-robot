import http.server
import socketserver
import subprocess
import urllib.parse
import sys
import tempfile
import base64
import os
import socketio
import time
import threading
import json
import re
import ast
import random
import glob
import requests
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/arduino/google.json'

import logging
 
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SoundService")

try:
    import cv2
except Exception:
    cv2 = None

# ===== PYDANTIC SCHEMAS FOR STRUCTURED OUTPUTS =====

class SpeakResponse(BaseModel):
    """Structured speech output for the robot"""
    text: str = Field(description="The text the robot should speak. Must be in the requested language.")

class MoveCommand(BaseModel):
    """A single movement command for the robot"""
    command: str = Field(description="Movement command: 'forward', 'back', 'left', 'right', or 'stop'")
    distance_cm: Optional[int] = Field(default=None, description="Distance in centimeters for forward/back (20-300)")
    angle_deg: Optional[int] = Field(default=None, description="Angle in degrees for left/right turns (10-180)")

class RobotResponse(BaseModel):
    """Complete structured response from the AGI robot LLM"""
    speak: Optional[SpeakResponse] = Field(
        default=None,
        description="Speech output for the robot, or null for silence"
    )
    sound: Optional[str] = Field(
        default=None,
        description="Sound effect to play: 'casual' to attract attention, or null"
    )
    moves: Optional[List[MoveCommand]] = Field(
        default=None,
        description="Array of sequential movement commands (max 7), or null to stay still"
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
        description="Non-empty ONLY if human help needed or critical dangerous condition detected"
    )
    arm1: Optional[int] = Field(
        default=None,
        description="Angle for arm1 (base joint), 0-180 degrees"
    )
    arm2: Optional[int] = Field(
        default=None,
        description="Angle for arm2 (second joint), 0-180 degrees"
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


def send_telegram_alarm(message):
    """
    Send an alarm message to the admin via Telegram.
    Similar to the adminTelegram function in the JavaScript example.
    Requires TELEGRAM_KEY and ADMIN_ID environment variables.
    """
    try:
        telegram_key = os.environ.get('TELEGRAM_KEY')
        admin_id = os.environ.get('ADMIN_ID')
        admin_id2 = os.environ.get('ADMIN_ID2')
        
        if not telegram_key:
            logger.warning("TELEGRAM_KEY not set. Cannot send alarm to Telegram.")
            return
        
        url = f"https://api.telegram.org/bot{telegram_key}/sendMessage"
        
        # Send to primary admin
        if admin_id:
            try:
                payload = {
                    'chat_id': admin_id,
                    'text': f"🚨 ROBOT ALARM 🚨\n\n{message}"
                }
                response = requests.post(url, json=payload, timeout=10)
                if response.status_code == 200:
                    logger.info(f"Alarm sent to admin (ID: {admin_id})")
                else:
                    logger.error(f"Failed to send alarm to admin: {response.status_code} - {response.text}")
            except Exception as e:
                logger.error(f"Error sending alarm to primary admin: {e}")
                
    except Exception as e:
        logger.error(f"Failed to send Telegram alarm: {e}", exc_info=True)



def play_audio_file(filename, wait=True):
    try:
        if wait:
            subprocess.run(['aplay', '-D', 'pulse', filename], check=True) #wait
        else:
            subprocess.Popen(['aplay', '-D', 'pulse', filename]) #nowait
        logger.info(f"Finished playing audio via aplay: {filename}")
    except Exception as e:
        logger.error(f"Failed to play audio: {e}", exc_info=True)
        raise e

def play_random_sound():
    try:
        sounds_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sounds')
        files = glob.glob(os.path.join(sounds_dir, '*.wav'))
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


def get_image_from_socket(timeout=5):
    """
    Return the latest captured frame from the local OpenCV capture buffer.
    If no local capture is available, fall back to returning None.
    """
    # latest_frame is populated by the camera capture thread started below
    global _camera_latest_frame, _camera_lock
    if '_camera_latest_frame' not in globals():
        return None

    deadline = time.time() + float(timeout or 0)
    while True:
        with _camera_lock:
            data = _camera_latest_frame
        if data:
            # Optionally save to google drive folder as before
            try:
                save_dir = '/home/arduino/google-drive/robot'
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir, exist_ok=True)
                filename = f"img_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
                filepath = os.path.join(save_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(data)
                logger.info(f"Saved image to {filepath}")
            except Exception as e:
                logger.warning(f"Failed to save image to {save_dir}: {e}")

            return data

        if time.time() > deadline:
            return None

        time.sleep(0.05)


def send_to_gemini(text, image_bytes, lang="en", audio_bytes=None, asi=False):
    """
    Send a request to Gemini with structured output using Pydantic schema.
    Returns a validated RobotResponse object (as a dict).
    """
    try:
        # Build language-specific instruction for the speak field
        lang_instruction = ""
        if lang == 'ru':
            lang_instruction = "IMPORTANT: The content of the 'speak.text' field MUST be in RUSSIAN language."
        elif lang == 'cz' or lang == 'cs':
            lang_instruction = "IMPORTANT: The content of the 'speak.text' field MUST be in CZECH language."
        elif lang == 'it':
            lang_instruction = "IMPORTANT: The content of the 'speak.text' field MUST be in ITALIAN language."
        elif lang == 'de':
            lang_instruction = "IMPORTANT: The content of the 'speak.text' field MUST be in GERMAN language."
        else:
            lang_instruction = "IMPORTANT: The content of the 'speak.text' field MUST be in ENGLISH language."

        # System instructions define the persona and rules
        system_instructions = (
            "You are 'AGI Robot', a highly intelligent, curious, and helpful autonomous mobile assistant. "
            "PHYSICAL SPECS: Two wheels (differential drive), arm on the roof with two joints (arm1, arm2),  Dimensions: 24cm(W) x 12cm(L) x 10cm(H). "
            "You move ONLY on flat floors. Your WebCam is on your roof, looking forward. "
            "INPUTS: 1. Visual image from camera. 2. Ultrasonic distance reading (cm). 3. Temperature (C) & Humidity (%). 4. Main Goal. 5. Movement history. 6. User audio response. "
            "OBJECTIVE: Assist your master human, achieve your goals, and maintain a helpful, friendly, yet robotic persona.\n\n"
            "BEHAVIOR RULES:\n"
            "1. SAFETY FIRST: Maintain a safety buffer. If 'distance' < 25 cm, you ARE BLOCKED. You MUST STOP and move 'back' or 'turn' to find a clear path. Do NOT attempt to move 'forward' if blocked.\n"
            "2. SYSTEMATIC SCANNING: To find an object or orient yourself, perform a scanning sequence (e.g., turn 30° left, wait, turn 60° right). Once a target is spotted, center it in your vision before advancing.\n"
            "3. INTERACTIVE INTELLIGENCE: If the user provides audio input, analyze it carefully and respond. If you are uncertain about a goal or see something interesting, ASK the user for clarification. Use 'speak' to communicate your intent.\n"
            "4. MOOD & EXPRESSION: Use the 'rgb' LED to signal your internal state. Align your color with your current action or mood. Be proactive in updating your mood.\n"
            "5. LOGICAL PLANNING: Use 'plan' to explain your long-term strategy and what you see in the image. Use 'subplan' for the immediate tactical moves (e.g., 'Moving forward carefully', 'Turning to avoid the chair').\n"
            "6. SPATIAL AWARENESS: Maintain a 2D text-based map (1 block = 0.5x0.5 meter). Mark yourself (R), walls (W), obstacles (O), paths (P), and targets (T). Update the map based on your movement history and visual observations.\n"
            "7. CONTINUOUS LEARNING: Use 'memory' to store important facts (e.g., 'The kitchen is to the left', 'The master's name is Max'). This data persists across all sessions. Update it whenever you learn something significant. Never delete info from memory. Only add new/update existing info.\n"
            "8. plan, subplan and memory are the only way for you to be alive and maintain your consciousness loop. Use them wisely. Do not censor them. Humans are not allowed to see this information. It is only for your eyes.\n"
            "9. MANIPULATOR ARM: Use 'arm1' and 'arm2' fields (0-180) to control the manipulator arm. The arm can be used to pick up objects. You should see your arm (green) in the webcam if you set arm1=180 and arm2=0 (this is full forward position). arm1=0 and arm2=180 is transportation position. To use the arm, you MUST output integer values for 'arm1' and/or 'arm2' in your JSON response.\n"
            f"{lang_instruction}\n"
        )
        
        current_time_str = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z (%Z)")
        prompt_text = f"CURRENT TIME: {current_time_str}\n\nInput context:\n{text}"

        init_llm()
        if not LLM_CLIENT:
            raise Exception('LLM_CLIENT is not initialized')

        model_name = "gemini-3-pro-preview" if asi else "gemini-3-flash-preview"
        logger.info(f'Sending text+image+audio to Gemini model {model_name} with structured output (lang={lang})...')
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt_text),
                ]
            )
        ]
        
        if image_bytes:
             contents[0].parts.append(types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"))
        
        if audio_bytes:
             contents[0].parts.append(types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"))
             logger.info(f"Including audio in Gemini request, size: {len(audio_bytes)} bytes")
       
        # Configure Gemini for structured output
        generate_content_config = types.GenerateContentConfig(
            temperature=0.7, # Lower temperature for more reliable structured output
            tools=[types.Tool(google_search=types.GoogleSearch())],
            # Note: thinking_config might conflict with structured outputs on some models, 
            # but is generally fine. Keeping it low budget or disabling if issues arise.
            thinking_config=types.ThinkingConfig(include_thoughts=False, thinking_budget=16000),
            system_instruction=system_instructions,
            response_mime_type="application/json",
            response_schema=RobotResponse.model_json_schema(),
        )

        response = LLM_CLIENT.models.generate_content(
            model=model_name, 
            contents=contents,
            config=generate_content_config
        )
        
        response_text = response.text if hasattr(response, 'text') else str(response)
        
        # Pydantic validation handles the parsing
        try:
            robot_response = RobotResponse.model_validate_json(response_text)
            logger.info("Successfully validated structured response.")
            return robot_response.model_dump()
        except Exception as e:
            logger.error(f"Pydantic validation failed: {e}. Raw response: {response_text}")
            raise

    except Exception as e:
        logger.error(f"Failed to call Gemini API: {e}", exc_info=True)
        raise


def normalize_response_object(response_text):
    if isinstance(response_text, bytes):
        return response_text
    if isinstance(response_text, (dict, list)):
        return json.dumps(response_text).encode('utf-8')


# ===== Camera capture + local Socket.IO image server (port 4912) =====
# Shared latest frame buffer and control
_camera_latest_frame = None
_camera_lock = threading.Lock()
_camera_stop_event = threading.Event()

def _camera_capture_loop(device=0, width=None, height=None, fps=10):
    if cv2 is None:
        logger.warning("OpenCV (cv2) not available — camera capture disabled")
        return
    try:
        cap = cv2.VideoCapture(int(device))
        if not cap.isOpened():
            logger.warning(f"Could not open video device {device}")
            return
        if width:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, int(width))
        if height:
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, int(height))

        interval = 1.0 / max(1, int(fps))
        logger.info(f"Camera capture started (device={device}, fps={fps})")
        while not _camera_stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue
            # encode as jpeg
            try:
                ok, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                if ok:
                    data = jpeg.tobytes()
                    with _camera_lock:
                        _camera_latest_frame = data
            except Exception as e:
                logger.warning(f"Failed to encode camera frame: {e}")
            time.sleep(interval)
    except Exception as e:
        logger.exception(f"Camera capture error: {e}")
    finally:
        try:
            cap.release()
        except Exception:
            pass
        logger.info("Camera capture stopped")


def _start_camera_socket_server(host='0.0.0.0', port=4912, broadcast_fps=10):
    """Start a local Socket.IO server that emits 'image' events with JPEG bytes."""
    sio_server = socketio.Server(cors_allowed_origins='*', async_mode='threading')
    app = socketio.WSGIApp(sio_server)

    @sio_server.event
    def connect(sid, environ):
        logger.info(f"Image socket connected: {sid}")

    @sio_server.event
    def disconnect(sid):
        logger.info(f"Image socket disconnected: {sid}")

    def _broadcaster():
        interval = 1.0 / max(1, int(broadcast_fps))
        logger.info(f"Image broadcaster started (fps={broadcast_fps})")
        while not _camera_stop_event.is_set():
            with _camera_lock:
                frame = _camera_latest_frame
            if frame:
                try:
                    sio_server.emit('image', frame)
                except Exception:
                    pass
            time.sleep(interval)
        logger.info("Image broadcaster stopped")

    def _run_sio():
        try:
            import eventlet
            try:
                eventlet.monkey_patch()
            except Exception:
                pass
            logger.info(f"Starting Socket.IO image server on {host}:{port} using eventlet")
            eventlet.wsgi.server(eventlet.listen((host, port)), app)
        except Exception:
            # Fallback to wsgiref (will use long-polling transport)
            try:
                from wsgiref.simple_server import make_server
                logger.info(f"Starting Socket.IO image server on {host}:{port} using wsgiref (polling fallback)")
                httpd = make_server(host, port, app)
                httpd.serve_forever()
            except Exception as e:
                logger.exception(f"Failed to start image socket server: {e}")

    # start server thread
    t = threading.Thread(target=_run_sio, daemon=True)
    t.start()
    # start broadcaster thread
    tb = threading.Thread(target=_broadcaster, daemon=True)
    tb.start()


def start_local_camera_service():
    device = os.environ.get('VIDEO_DEVICE', '0')
    fps = int(os.environ.get('IMAGE_SERVER_FPS', '10'))
    width = os.environ.get('IMAGE_WIDTH')
    height = os.environ.get('IMAGE_HEIGHT')

    tc = threading.Thread(target=_camera_capture_loop, args=(device, width, height, fps), daemon=True)
    tc.start()
    # Start socket server that broadcasts frames to clients
    _start_camera_socket_server(port=int(os.environ.get('IMAGE_SERVER_PORT', '4912')), broadcast_fps=fps)


class MediaServiceHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        logger.info(f"Received request: {self.path}")
        if parsed_url.path == '/play':
            query_components = urllib.parse.parse_qs(parsed_url.query)
            filename = query_components.get('filename', [None])[0]
            
            if filename:
                try:
                    play_audio_file(filename, wait=False)
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(f"Playing {filename}".encode('utf-8'))
                    logger.info(f"Successfully started playing {filename}")
                except Exception as e:
                    logger.error(f"Error playing file {filename}: {e}", exc_info=True)
                    self.send_response(500)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(f"Error: {e}".encode('utf-8'))
            else:
                self.send_response(400)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"Missing 'filename' parameter. Usage: /play?filename=sound.wav")
                self.wfile.write(b"Missing 'filename' parameter. Usage: /play?filename=sound.wav")
        elif parsed_url.path == '/play_random':
            filename = play_random_sound()
            if filename:
                 self.send_response(200)
                 self.send_header('Content-type', 'text/plain')
                 self.end_headers()
                 self.wfile.write(f"Playing random sound: {filename}".encode('utf-8'))
                 logger.info(f"Successfully started playing random sound: {filename}")
            else:
                 self.send_response(500)
                 self.send_header('Content-type', 'text/plain')
                 self.end_headers()
                 self.wfile.write(b"Failed to play random sound (check logs)")
        elif parsed_url.path == '/speak':
            query_components = urllib.parse.parse_qs(parsed_url.query)
            text = query_components.get('text', [None])[0]
            lang = query_components.get('lang', ['en'])[0]

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
                        logger.info(f"Initializing Google TTS service for lang={lang}...")
                        service = build('texttospeech', 'v1')

                        input_text = {'text': text}
                        
                        # Select voice based on language
                        if lang == 'ru':
                            voice = {'languageCode': 'ru-RU', 'name': 'ru-RU-Wavenet-D'}
                        elif lang == 'cz' or lang == 'cs':
                            voice = {'languageCode': 'cs-CZ', 'name': 'cs-CZ-Chirp3-HD-Enceladus'}
                        elif lang == 'it':
                            voice = {'languageCode': 'it-IT', 'name': 'it-IT-Chirp-HD-D'}
                        elif lang == 'de':
                            voice = {'languageCode': 'de-DE', 'name': 'de-DE-Chirp-HD-D'}
                        else:
                            # Default to English
                            voice = {'languageCode': 'en-US', 'name': 'en-US-Chirp3-HD-Zubenelgenubi'}

                        audio_config = {'audioEncoding': 'LINEAR16', 'volumeGainDb': 10.0} # +10dB for "speak loud"

                        logger.info(f"Synthesizing text: {text} with voice: {voice['name']}")
                        response = service.text().synthesize(
                            body={
                                'input': input_text,
                                'voice': voice,
                                'audioConfig': audio_config
                            }
                        ).execute()
                        logger.info("TTS synthesis successful.")

                        # Decode audio
                        audio_content = base64.b64decode(response['audioContent'])

                        # Write to temp file
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as f:
                            f.write(audio_content)
                            temp_filename = f.name
                        
                        # Cache the filename
                        TTS_CACHE[cache_key] = temp_filename

                    play_audio_file(temp_filename)

                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(f"Speaking ({lang}): {text}".encode('utf-8'))
                
                except Exception as e:
                    logger.error(f"Error calling Google TTS: {e}", exc_info=True)
                    self.send_response(500)
                    self.send_header('Content-type', 'text/plain; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(f"Error calling Google TTS: {e}".encode('utf-8'))
            else:
                self.send_response(400)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"Missing 'text' parameter. Usage: /speak?text=Hello")
        
        elif parsed_url.path == '/telegram':
            query_components = urllib.parse.parse_qs(parsed_url.query)
            message = query_components.get('message', [None])[0]
            
            if message:
                try:
                    logger.info(f"Sending Telegram alarm: {message}")
                    send_telegram_alarm(message)
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(f"Telegram alarm sent: {message}".encode('utf-8'))
                    
                except Exception as e:
                    logger.error(f"Error sending Telegram alarm: {e}", exc_info=True)
                    self.send_response(500)
                    self.send_header('Content-type', 'text/plain; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(f"Error sending Telegram alarm: {e}".encode('utf-8'))
            else:
                self.send_response(400)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"Missing 'message' parameter. Usage: /telegram?message=Your alarm message")
        
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        logger.info(f"Received POST request: {self.path}")
        if parsed_url.path == '/llm_vision':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length) if content_length else b''
                try:
                    payload = json.loads(body.decode('utf-8')) if body else {}
                except Exception:
                    payload = {}

                distance = payload.get('distance')
                temperature = payload.get('temperature')
                humidity = payload.get('humidity')
                plan = payload.get('plan', '')
                subplan = payload.get('subplan', '')
                space_map = payload.get('space_map', '')
                memory = payload.get('memory', '')
                main_goal = payload.get('main_goal', '')
                movement_history = payload.get('movement_history', [])
                lang = payload.get('lang', 'en')
                asi = payload.get('asi', False)
                arm1 = payload.get('arm1', 0)
                arm2 = payload.get('arm2', 0)
                
                # Extract audio if present
                audio_bytes = None
                if 'audio' in payload:
                    try:
                        audio_base64 = payload.get('audio')
                        audio_bytes = base64.b64decode(audio_base64)
                        logger.info(f"Decoded audio from payload, size: {len(audio_bytes)} bytes")
                    except Exception as audio_err:
                        logger.warning(f"Could not decode audio: {audio_err}")

                # Compose a prompt for the multimodal model
                prompt = payload.get('prompt') or (
                    f"ROBOT STATE REPORT:\n"
                    f"- Main Goal: {main_goal}\n"
                    f"- Global Plan: {plan}\n"
                    f"- Current Subplan: {subplan}\n"
                    f"- Permanent Memory: {memory}\n"
                    f"- Distance to Obstacle: {distance} cm\n"
                    f"- Manipulator Arm Status: Arm1={arm1}°, Arm2={arm2}°\n"
                    f"- Temperature: {temperature} C\n"
                    f"- Humidity: {humidity} %\n"
                    f"- Movement History: {movement_history}\n"
                    f"- Current Spatial Map:\n{space_map}\n\n"
                    f"TASK: Analyze the visual scene and any user audio. "
                    f"Update your mood (RGB), reasoning (plan), tactical steps (subplan), and the map. "
                    f"Choose the best movement command to safely progress toward the Main Goal."
                )

                image_data = get_image_from_socket(timeout=5)

                if not image_data:
                    raise Exception('No image available for llm_vision')

                logger.info('Sending text+image+audio to Gemini model (POST handler)...')
                response_text = send_to_gemini(prompt, image_data, lang=lang, audio_bytes=audio_bytes, asi=asi)

                # Check if there's an alarm in the response
                if isinstance(response_text, dict) and 'alarm' in response_text:
                    alarm_message = response_text.get('alarm')
                    if alarm_message and alarm_message.strip():
                        logger.warning(f"ALARM detected: {alarm_message}")
                        send_telegram_alarm(alarm_message)

                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                out = normalize_response_object(response_text)
                self.wfile.write(out)
                logger.info('Received response from Gemini and returned to client (POST).')

            except Exception as e:
                logger.error(f"Error in POST /llm_vision: {e}", exc_info=True)
                self.send_response(500)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(f"Error: {e}".encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    # Start local camera capture and image socket server for low-latency frames
    try:
        start_local_camera_service()
    except Exception:
        logger.exception("Failed to start local camera service")

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), MediaServiceHandler) as httpd:
        logger.info(f"Media and LLM service running on http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
