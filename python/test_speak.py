import urllib.request
import urllib.parse
import sys

def speak(text):
    # Try localhost first, then the specific IP used in main.py
    # This covers running locally or accessing a container
    hosts = ["localhost", "127.0.0.1"]
    
    for host in hosts:
        try:
            print(f"Attempting to connect to sound service at {host}...")
            query = urllib.parse.urlencode({'text': text})
            url = f"http://{host}:5000/speak?{query}"
            
            # Using a timeout to fail fast if the host is unreachable
            with urllib.request.urlopen(url, timeout=5) as response:
                result = response.read().decode('utf-8')
                print(f"Success! Response: {result}")
                return
        except Exception as e:
            print(f"Failed to connect to {host}: {e}")

    print("Could not reach sound service on any configured host.")

if __name__ == "__main__":
    # Check if a command line argument is provided, otherwise use default
    text_to_speak = "Привет проверка связи" # "Hello communication check"
    
    if len(sys.argv) > 1:
        text_to_speak = " ".join(sys.argv[1:])
        
    speak(text_to_speak)
