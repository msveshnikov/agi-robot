import http.server
import socketserver
import subprocess
import urllib.parse
import sys
import tempfile
import base64
import os

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
                # Store captured image in a temporary file
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                    image_path = f.name
                
                # Capture command (fswebcam for Debian)
                if sys.platform != 'win32':
                    # -r resolution, --no-banner removes timestamp banner, -S skips frames for auto-exposure
                    cmd = ['fswebcam', '-d', '/dev/video0', '-r', '1280x720', '--no-banner', '-S', '5', image_path]
                    logger.info(f"Capturing image with command: {' '.join(cmd)}")
                    subprocess.run(cmd, check=True, capture_output=True)
                else:
                    # Windows placeholder or error (fswebcam not standard on Windows)
                    # For now, just return an error or bytes of a dummy image could be created, 
                    # but easiest is to report not supported or try a generic approach if possible.
                    # We will raise error to be clear functionality is for Debian as requested.
                    raise NotImplementedError("Camera capture not implemented for Windows in this script.")

                with open(image_path, 'rb') as f:
                    image_data = f.read()
                
                # Clean up temp file
                os.remove(image_path)

                self.send_response(200)
                self.send_header('Content-type', 'image/jpeg')
                self.send_header('Content-length', str(len(image_data)))
                self.end_headers()
                self.wfile.write(image_data)
                logger.info("Image captured and sent.")

            except subprocess.CalledProcessError as e:
                logger.error(f"Error executing fswebcam: {e.stderr}", exc_info=True)
                self.send_response(500)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(f"Error capturing image: {e}".encode('utf-8'))
            except Exception as e:
                logger.error(f"Error in /camera endpoint: {e}", exc_info=True)
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
        logger.info(f"Sound player service running on http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
