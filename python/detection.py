import pyaudio
import numpy as np
import sys
sys.stdout.reconfigure(encoding='utf-8')
from openwakeword.model import Model

# Загружаем модель (она скачается сама при первом запуске)
# Можно выбрать: 'hey_jarvis', 'alexa', 'hey_mycroft', 'hey_google'
model = Model(
    wakeword_models=["hey_jarvis"], 
    inference_framework="onnx"
)
# Настройки микрофона
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1280 # openWakeWord любит куски по 1280 сэмплов (80 мс)

audio = pyaudio.PyAudio()
mic_stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

print("🎧 Скажите 'Hey Jarvis'...")

try:
    while True:
        # Читаем аудио с микрофона
        data = np.frombuffer(mic_stream.read(CHUNK), dtype=np.int16)
        
        # Скармливаем модели
        prediction = model.predict(data)
        
        # prediction - это словарь, например {'hey_jarvis': 0.002}
        # Проверяем уверенность модели (обычно > 0.5 считается срабатыванием)
        if prediction["hey_jarvis"] > 0.5:
            print("🤖 О! Вы меня позвали! (Запускаю запись...)")
            
            # --- ТУТ ВАШ КОД ДЛЯ ЗАПИСИ (как в примере выше) ---
            # Не забудьте сбросить буфер модели, чтобы она не сработала дважды подряд
            model.reset()

except KeyboardInterrupt:
    pass
finally:
    mic_stream.stop_stream()
    mic_stream.close()
    audio.terminate()