import http.server
import socketserver
import subprocess
import urllib.parse
import sys
import tempfile
import base64
import os
#os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'C:\\My-progs\\Arduino\\google.json'
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
