import http.server
import socketserver
import subprocess
import urllib.parse
import tempfile
import base64
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/arduino/google.json'
try:
    from googleapiclient.discovery import build
except ImportError:
    print("Warning: google-api-python-client not found. TTS will not work.")


PORT = 5000

class SoundPlayerHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path == '/play':
            query_components = urllib.parse.parse_qs(parsed_url.query)
            filename = query_components.get('filename', [None])[0]
            
            if filename:
                try:
                    # Execute 'aplay filename'
                    # Use Popen to play asynchronously so the request doesn't block the web server
                    subprocess.Popen(['aplay', filename])
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(f"Playing {filename}".encode('utf-8'))
                except Exception as e:
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
                    service = build('texttospeech', 'v1')

                    input_text = {'text': text}
                    voice = {'languageCode': 'ru-RU', 'name': 'ru-RU-Wavenet-C'}
                    audio_config = {'audioEncoding': 'LINEAR16', 'volumeGainDb': 10.0} # +10dB for "speak loud"

                    response = service.text().synthesize(
                        body={
                            'input': input_text,
                            'voice': voice,
                            'audioConfig': audio_config
                        }
                    ).execute()

                    # Decode audio
                    audio_content = base64.b64decode(response['audioContent'])

                    # Write to temp file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as f:
                        f.write(audio_content)
                        temp_filename = f.name

                    # Play audio using aplay
                    subprocess.Popen(['aplay', temp_filename])

                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(f"Speaking: {text}".encode('utf-8'))
                
                except Exception as e:
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
        print(f"Sound player service running on http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
