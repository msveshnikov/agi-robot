import json
import pyaudio
from vosk import Model, KaldiRecognizer

# Скачайте модель "vosk-model-small-ru-0.22" и распакуйте в папку 'model'
model = Model("model")
rec = KaldiRecognizer(model, 16000)

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4000)
stream.start_stream()

print("Слушаю...")

while True:
    data = stream.read(4000, exception_on_overflow=False)
    if rec.AcceptWaveform(data):
        result = json.loads(rec.Result())
        text = result.get('text', '')
        if "робот" in text or "джарвис" in text:
            print("Распознано ключевое слово!")