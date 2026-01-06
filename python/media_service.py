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

if sys.platform == 'win32':
  os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'C:\\My-progs\\Arduino\\google.json'
else:
  os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/arduino/google.json'

import logging

# Configure logging
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
    import google.auth
    import vertexai
    from vertexai.generative_models import GenerativeModel
except ImportError:
    logger.warning("google-cloud-aiplatform not found. LLM will not work.")

try:
    import requests
except Exception:
    requests = None
def play_audio_file(filename):
    try:
        if sys.platform == 'win32':
            import winsound
            # SND_FILENAME: filename is a file name
            # SND_ASYNC: play asynchronously
            # SND_NODEFAULT: do not play default sound if file not found
            winsound.PlaySound(filename, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
            logger.info(f"Playing audio on Windows: {filename}")
        else:
            # Linux / other
            subprocess.Popen(['aplay', filename])
            logger.info(f"Playing audio via aplay: {filename}")
    except Exception as e:
        logger.error(f"Failed to play audio: {e}", exc_info=True)
        raise e


PORT = 5000
TTS_CACHE = {}
LLM_MODEL = None

def init_llm():
    global LLM_MODEL
    if LLM_MODEL:
        return
    
    try:
        # Credentials are automatically loaded from GOOGLE_APPLICATION_CREDENTIALS env var
        credentials, project_id = google.auth.default()
        vertexai.init(project=project_id, location="us-central1", credentials=credentials)
        LLM_MODEL = GenerativeModel("gemini-2.5-flash")
        logger.info("Vertex AI initialized with Gemini")
    except Exception as e:
        logger.error(f"Failed to initialize Vertex AI: {e}", exc_info=True)
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


def send_to_gemini(text, image_bytes):
    try:
        # Build a prompt that forces a JSON-only response matching the expected schema
        schema_instructions = (
            "Return ONLY a single valid JSON object (no explanatory text) with the following keys:\n"
            "- speak: either null or an object {\"text\": string}\n"
            "- move: either null or an object {\"command\": one of [\"forward\",\"back\",\"left\",\"right\",\"stop\"],\n"
            "         \"distance_cm\": integer or null, \"angle_deg\": integer or null, \"speed\": integer or null }\n"
            "- subplan: a string (may be empty)\n"
            "Do not include any other keys or text. Make sure the JSON parses with standard JSON parsers."
        )

        prompt_text = f"{schema_instructions}\n\nInput context:\n{text}"

        # Prefer using the vertexai client (same as /llm) if available.
        try:
            init_llm()
            if LLM_MODEL:
                logger.info('Using Vertex AI client for Gemini (via vertexai)')
                try:
                    response = LLM_MODEL.generate_content(prompt_text)
                    if hasattr(response, 'text'):
                        response_text = response.text
                    else:
                        response_text = str(response)

                    # Try to parse JSON and return parsed object if valid
                    try:
                        return json.loads(response_text)
                    except Exception:
                        # Attempt to extract JSON substring
                        m = re.search(r"\{[\s\S]*\}", response_text)
                        if m:
                            try:
                                return json.loads(m.group(0))
                            except Exception:
                                pass
                        # Fallthrough to allow REST fallback below
                        logger.warning('Vertex AI returned non-json, raw: %s', response_text)
                        # attempt a conversion pass below
                except Exception:
                    logger.exception('Vertex AI client call failed, falling back to REST API')
        except Exception:
            logger.exception('Failed to initialize Vertex AI client; will try REST generativemodels API')

        # Try using google.auth credentials to call Generative Models REST API
        # Request a token with the cloud-platform scope so the REST API accepts it
        credentials, project_id = google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
        from google.auth.transport.requests import Request
        credentials.refresh(Request())
        token = credentials.token

        if not requests:
            raise Exception('requests package not available')

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        body = {
            'instances': [
                {
                    'input': {
                        'text': prompt_text,
                        'image': {
                            'mime_type': 'image/jpeg',
                            'data': base64.b64encode(image_bytes).decode('utf-8')
                        }
                    }
                }
            ],
            'parameters': {
                'temperature': 0.2
            }
        }

        # Try a list of Gemini model endpoints, preferring Flash 2.5 for vision.
        model_candidates = [
            'gemini-2.5-flash',
            'gemini-2.5-flash-preview',
            'gemini-robotics-er-1.5-preview'
        ]

        resp = None
        last_exc = None
        for model_name in model_candidates:
            try:
                url = f'https://generativemodels.googleapis.com/v1/models/{model_name}:predict'
                resp = requests.post(url, headers=headers, json=body, timeout=30)
                # If we get a 404 try next model; otherwise break and handle response
                if resp.status_code == 404:
                    resp = None
                    continue
                break
            except Exception as e:
                last_exc = e
                resp = None
                continue

        if resp is None:
            if last_exc:
                raise last_exc
            raise Exception('No response from any Gemini model endpoints')

        if resp.status_code != 200:
            raise Exception(f'Non-200 from Gemini API: {resp.status_code} {resp.text}')

        j = resp.json()
        # Try to extract reasonable text response from known fields
        response_text = None
        if 'predictions' in j and isinstance(j['predictions'], list) and j['predictions']:
            pred = j['predictions'][0]
            # Common fields: 'content', 'output', 'text'
            for key in ('content', 'output', 'text', 'candidates'):
                if key in pred:
                    val = pred[key]
                    if isinstance(val, str):
                        response_text = val
                        break
                    if isinstance(val, list) and val:
                        if isinstance(val[0], dict) and 'content' in val[0]:
                            response_text = val[0]['content']
                            break
                        response_text = str(val)
                        break

        if response_text is None:
            # fallback to full JSON string
            response_text = json.dumps(j)

        # Try to parse JSON directly
        try:
            return json.loads(response_text)
        except Exception:
            # Try extracting JSON substring
            m = re.search(r"\{[\s\S]*\}", response_text)
            if m:
                try:
                    return json.loads(m.group(0))
                except Exception:
                    pass

        # If available, ask Vertex AI to convert the raw text into valid JSON matching schema
        try:
            init_llm()
            if LLM_MODEL:
                convert_prompt = (
                    "Convert the following text into a single valid JSON object matching the schema:\n"
                    f"{schema_instructions}\n\nRaw text:\n{response_text}\n\nReturn only the JSON object."
                )
                logger.info('Requesting JSON conversion from Vertex AI for non-JSON output')
                conv_resp = LLM_MODEL.generate_content(convert_prompt)
                conv_text = conv_resp.text if hasattr(conv_resp, 'text') else str(conv_resp)
                try:
                    return json.loads(conv_text)
                except Exception:
                    m2 = re.search(r"\{[\s\S]*\}", conv_text)
                    if m2:
                        try:
                            return json.loads(m2.group(0))
                        except Exception:
                            pass
        except Exception:
            logger.exception('JSON conversion via Vertex AI failed')

        # Final fallback: raise to allow caller to handle non-json
        raise Exception('Gemini returned non-JSON and conversion attempts failed')

    except Exception as e:
        logger.error(f"Failed to call Gemini API: {e}", exc_info=True)
        raise

class SoundPlayerHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        logger.info(f"Received request: {self.path}")
        if parsed_url.path == '/play':
            query_components = urllib.parse.parse_qs(parsed_url.query)
            filename = query_components.get('filename', [None])[0]
            
            if filename:
                try:
                    # Execute 'aplay filename' or winsound
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
        elif parsed_url.path == '/speak':
            query_components = urllib.parse.parse_qs(parsed_url.query)
            text = query_components.get('text', [None])[0]

            if text:
                try:
                    if text in TTS_CACHE:
                        logger.info(f"Using cached audio for text: {text}")
                        temp_filename = TTS_CACHE[text]
                    else:
                        # Initialize TTS service
                        # Note: Requires GOOGLE_APPLICATION_CREDENTIALS environment variable to be set
                        logger.info("Initializing Google TTS service...")
                        service = build('texttospeech', 'v1')

                        input_text = {'text': text}
                        voice = {'languageCode': 'ru-RU', 'name': 'ru-RU-Wavenet-B'}
                        audio_config = {'audioEncoding': 'LINEAR16', 'volumeGainDb': 10.0} # +10dB for "speak loud"

                        logger.info(f"Synthesizing text: {text}")
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
                        TTS_CACHE[text] = temp_filename

                    # Play audio using aplay
                    play_audio_file(temp_filename)

                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(f"Speaking: {text}".encode('utf-8'))
                
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
        
        elif parsed_url.path == '/camera':
            try:
                # Use shared socket image helper
                image_data = get_image_from_socket(timeout=5)

                if not image_data:
                    raise Exception('No image received from socket provider')

                self.send_response(200)
                self.send_header('Content-type', 'image/jpeg')
                self.send_header('Content-length', str(len(image_data)))
                self.end_headers()
                self.wfile.write(image_data)
                logger.info('Image received from socket provider and sent.')

            except Exception as e:
                logger.error(f"Error in /camera endpoint: {e}", exc_info=True)
                self.send_response(500)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(f"Error: {e}".encode('utf-8'))
        
        elif parsed_url.path == '/llm':
            query_components = urllib.parse.parse_qs(parsed_url.query)
            prompt = query_components.get('text', [None])[0]

            if prompt:
                try:
                    init_llm()
                    if not LLM_MODEL:
                        raise Exception("LLM model not initialized")
                    
                    logger.info(f"Generating text for prompt: {prompt}")
                    # Generate content
                    response = LLM_MODEL.generate_content(prompt)
                    generated_text = response.text
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(generated_text.encode('utf-8'))
                    logger.info("LLM generation successful.")

                except Exception as e:
                    logger.error(f"Error calling Vertex AI LLM: {e}", exc_info=True)
                    self.send_response(500)
                    self.send_header('Content-type', 'text/plain; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(f"Error calling LLM: {e}".encode('utf-8'))
            else:
                self.send_response(400)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"Missing 'text' parameter. Usage: /llm?text=Hello")
        elif parsed_url.path == '/llm_vision':
            query_components = urllib.parse.parse_qs(parsed_url.query)
            prompt = query_components.get('text', [None])[0]

            if not prompt:
                self.send_response(400)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"Missing 'text' parameter. Usage: /llm_vision?text=Describe%20this")
            else:
                try:
                    # Capture image via socket provider
                    image_data = get_image_from_socket(timeout=5)
                    if not image_data:
                        raise Exception('No image available from socket provider')

                    # Send to Gemini multimodal model
                    logger.info('Sending text+image to Gemini model...')
                    response_text = send_to_gemini(prompt, image_data)

                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain; charset=utf-8')
                    self.end_headers()
                    if isinstance(response_text, bytes):
                        self.wfile.write(response_text)
                    else:
                        self.wfile.write(str(response_text).encode('utf-8'))
                    logger.info('Received response from Gemini and returned to client.')

                except Exception as e:
                    logger.error(f"Error in /llm_vision: {e}", exc_info=True)
                    self.send_response(500)
                    self.send_header('Content-type', 'text/plain; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(f"Error: {e}".encode('utf-8'))
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
                subplan = payload.get('subplan', '')
                main_goal = payload.get('main_goal', '')
                # Compose a prompt for the multimodal model
                prompt = payload.get('prompt') or f"Main goal: {main_goal}\nSubplan: {subplan}\nDistance: {distance}\nDescribe the scene and suggest next actions."

                image_data = None
                image_b64 = payload.get('image_base64')
                if image_b64:
                    try:
                        image_data = base64.b64decode(image_b64)
                    except Exception:
                        image_data = None

                if not image_data:
                    image_data = get_image_from_socket(timeout=5)

                if not image_data:
                    raise Exception('No image available for llm_vision')

                logger.info('Sending text+image to Gemini model (POST handler)...')
                response_text = send_to_gemini(prompt, image_data)

                self.send_response(200)
                self.send_header('Content-type', 'text/plain; charset=utf-8')
                self.end_headers()
                if isinstance(response_text, bytes):
                    self.wfile.write(response_text)
                else:
                    self.wfile.write(str(response_text).encode('utf-8'))
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
    # Allow address reuse to avoid "Address already in use" errors on restart
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), SoundPlayerHandler) as httpd:
        logger.info(f"Media and LLM service running on http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
