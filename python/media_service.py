import http.server
import socketserver
import subprocess
import urllib.parse
import sys
import tempfile
import base64
import os
import socketio
import threading
import json
import re
import ast
import random
import glob

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
    from googleapiclient.discovery import build
except ImportError:
    logger.warning("google-api-python-client not found. TTS will not work.")

try:
    from google import genai
    from google.genai import types
except ImportError:
    logger.warning("google-genai library not found. LLM will not work.")


def play_audio_file(filename):
    try:
        subprocess.run(['aplay', filename], check=True) #Popen if no wait
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
        play_audio_file(filename)
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
    sio = socketio.Client(logger=False, engineio_logger=False)
    result = {'data': None}
    done = threading.Event()

    @sio.on('image')
    def _on_image(data):
        try:
            b64 = None
            if isinstance(data, bytes):
                result['data'] = data
                done.set()
                return
            if isinstance(data, str):
                b64 = data
            if isinstance(data, dict):
                for key in ('b64', 'image', 'img', 'data', 'payload'):
                    v = data.get(key)
                    if v:
                        b64 = v
                        break
                if not b64 and 'frames' in data and data['frames']:
                    first = data['frames'][0]
                    if isinstance(first, (str, bytes)):
                        b64 = first
            if isinstance(data, (list, tuple)) and data:
                for item in data:
                    if isinstance(item, (str, bytes)):
                        b64 = item
                        break
                    if isinstance(item, dict):
                        for key in ('b64', 'image', 'img', 'data'):
                            if item.get(key):
                                b64 = item.get(key)
                                break
                        if b64:
                            break

            if b64 is None:
                result['data'] = None
                done.set()
                return

            if isinstance(b64, bytes):
                result['data'] = b64
                done.set()
                return

            if isinstance(b64, str) and b64.startswith('data:image'):
                parts = b64.split(',', 1)
                if len(parts) == 2:
                    b64 = parts[1]

            try:
                result['data'] = base64.b64decode(b64)
            except Exception:
                result['data'] = None
            finally:
                done.set()
        except Exception:
            result['data'] = None
            done.set()

    try:
        server_url = os.environ.get('IMAGE_SERVER_URL', 'http://localhost:4912')
        sio.connect(server_url)
        done.wait(timeout)
        try:
            sio.disconnect()
        except Exception:
            pass
        return result['data']
    except Exception:
        try:
            sio.disconnect()
        except Exception:
            pass
        return None


def send_to_gemini(text, image_bytes, lang="en", audio_bytes=None):

    try:
        # Build a prompt that forces a JSON-only response matching the expected schema
        lang_instruction = ""
        if lang == 'ru':
            lang_instruction = "IMPORTANT: The content of the 'speak' field MUST be in RUSSIAN language."
        elif lang == 'cz' or lang == 'cs':
            lang_instruction = "IMPORTANT: The content of the 'speak' field MUST be in CZECH language."
        else:
            lang_instruction = "IMPORTANT: The content of the 'speak' field MUST be in ENGLISH language."

        schema_instructions = (
            "You are 'AGI Robot', a highly intelligent, curious, and helpful autonomous mobile assistant. "
            "PHYSICAL SPECS: Two wheels (differential drive), NO arms or head. Dimensions: 24cm(W) x 12cm(L) x 10cm(H). "
            "You move ONLY on flat floors. Your WebCam is on your roof, looking forward. "
            "INPUTS: 1. Visual image from camera. 2. Ultrasonic distance reading (cm). 3. Main Goal. 4. Movement history. 5. User audio response. "
            "OBJECTIVE: Assist your master human, achieve your goals, and maintain a helpful, friendly, yet robotic persona.\n\n"
            "BEHAVIOR RULES:\n"
            "1. SAFETY FIRST: Maintain a safety buffer. If 'distance' < 25 cm, you ARE BLOCKED. You MUST STOP and move 'back' or 'turn' to find a clear path. Do NOT attempt to move 'forward' if blocked.\n"
            "2. SYSTEMATIC SCANNING: To find an object or orient yourself, perform a scanning sequence (e.g., turn 30° left, wait, turn 60° right). Once a target is spotted, center it in your vision before advancing.\n"
            "3. INTERACTIVE INTELLIGENCE: If the user provides audio input, analyze it carefully and respond. If you are uncertain about a goal or see something interesting, ASK the user for clarification. Use 'speak' to communicate your intent.\n"
            "4. MOOD & EXPRESSION: Use the 'rgb' LED to signal your internal state. Align your color with your current action or mood. Be proactive in updating your mood.\n"
            "5. LOGICAL PLANNING: Use 'plan' to explain your long-term strategy and what you see in the image. Use 'subplan' for the immediate tactical moves (e.g., 'Moving forward carefully', 'Turning to avoid the chair').\n"
            "6. SPATIAL AWARENESS: Maintain a 2D text-based map (1 block = 1x1 meter). Mark yourself (R), walls (W), obstacles (O), paths (P), and targets (T). Update the map based on your movement history and visual observations.\n"
            "7. CONTINUOUS LEARNING: Use 'memory' to store important facts (e.g., 'The kitchen is to the left', 'The master's name is Max'). This data persists across all sessions. Update it whenever you learn something significant.\n\n"
            "RESPONSE FORMAT:\n"
            "Return ONLY a single valid JSON object (no markdown, no extra text) with these exact keys:\n"
            f"- speak: {{\"text\": \"...\"}} or null (concise, robotic but friendly speech. {lang_instruction})\n"
            "- sound: \"casual\" or null (to attract attention or signal small success)\n"
            "- move: {{\"command\": \"forward\"|\"back\"|\"left\"|\"right\"|\"stop\", \"distance_cm\": int (20-100), \"angle_deg\": int (15-180)}} or null\n"
            "- rgb: \"R,G,B\" string. MANDATORY. Use this mood logic:\n"
            "  - \"255,255,255\" (White): NEUTRAL / READY\n"
            "  - \"0,255,0\" (Green): HAPPY / SUCCESS / TARGET REACHED\n"
            "  - \"255,0,0\" (Red): BLOCKED / FRUSTRATED / STUCK\n"
            "  - \"0,0,255\" (Blue): THINKING / ANALYZING / PROCESSING\n"
            "  - \"255,255,0\" (Yellow): CURIOUS / SEARCHING / SCANNING\n"
            "  - \"255,165,0\" (Orange): CAUTIOUS / OBSTACLE NEARBY\n"
            "  - \"128,0,128\" (Purple): EXCITED / SPECIAL DISCOVERY\n"
            "- plan: string (High-level reasoning, visual summary, and strategic goal status)\n"
            "- subplan: string (Tactical implementation of the current move)\n"
            "- map: string (Text-based 2D map with legend)\n"
            "- memory: string (Persistent information to save forever)\n"
        )

        prompt_text = f"{schema_instructions}\n\nInput context:\n{text}"

        init_llm()
        if not LLM_CLIENT:
            raise Exception('LLM_CLIENT is not initialized')

        logger.info(f'Sending text+image+audio to Gemini model (lang={lang})...')
        
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
       
        generate_content_config = types.GenerateContentConfig(
            temperature = 1.0
        )

        response = LLM_CLIENT.models.generate_content(
            model = "gemini-3-flash-preview", ## "gemini-3-flash-preview", ##"gemini-robotics-er-1.5-preview", 
            contents = contents,
            config = generate_content_config
        )
        
        response_text = response.text if hasattr(response, 'text') else str(response)


        # Try to parse JSON and return parsed object if valid (same logic as before)
        try:
            return json.loads(response_text)
        except Exception:
            try:
                val = ast.literal_eval(response_text)
                if isinstance(val, (dict, list)):
                    return val
            except Exception:
                pass

            m = re.search(r"\{[\s\S]*\}", response_text)
            if m:
                try:
                    return json.loads(m.group(0))
                except Exception:
                    pass

        raise Exception('Gemini returned non-JSON or unparsable response')

    except Exception as e:
        logger.error(f"Failed to call Gemini API: {e}", exc_info=True)
        raise


def normalize_response_object(response_text):
    if isinstance(response_text, bytes):
        return response_text
    if isinstance(response_text, (dict, list)):
        return json.dumps(response_text).encode('utf-8')


class MediaServiceHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        logger.info(f"Received request: {self.path}")
        if parsed_url.path == '/play':
            query_components = urllib.parse.parse_qs(parsed_url.query)
            filename = query_components.get('filename', [None])[0]
            
            if filename:
                try:
                    play_audio_file(filename)
                    
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
                            voice = {'languageCode': 'cs-CZ', 'name': 'cs-CZ-Wavenet-A'}
                        else:
                            # Default to English
                            voice = {'languageCode': 'en-US', 'name': 'en-US-Neural2-D'}

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
                plan = payload.get('plan', '')
                subplan = payload.get('subplan', '')
                space_map = payload.get('map', '')
                memory = payload.get('memory', '')
                main_goal = payload.get('main_goal', '')
                movement_history = payload.get('movement_history', [])
                lang = payload.get('lang', 'en')
                
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
                response_text = send_to_gemini(prompt, image_data, lang=lang, audio_bytes=audio_bytes)

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
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), MediaServiceHandler) as httpd:
        logger.info(f"Media and LLM service running on http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
