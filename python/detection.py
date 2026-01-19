import pyaudio
import numpy as np
import sys
import openwakeword
from openwakeword.model import Model

# Настройка кодировки консоли
sys.stdout.reconfigure(encoding='utf-8')

# --- СПЕЦИАЛЬНЫЙ КОД ДЛЯ ВЕРСИИ 0.4.0 ---

# 1. Получаем список путей ко всем скачанным моделям
all_model_paths = openwakeword.get_pretrained_model_paths()

# 2. Ищем путь конкретно к 'hey_jarvis'
jarvis_paths = [path for path in all_model_paths if "hey_jarvis" in path]

if not jarvis_paths:
    print("❌ Ошибка: Модель 'hey_jarvis' не найдена в установленных файлах.")
    print("Доступные модели:", all_model_paths)
    sys.exit(1)

print(f"✅ Загружаю модель из: {jarvis_paths[0]}")

# 3. Инициализируем модель (Обратите внимание: аргумент wakeword_model_paths)
model = Model(
    wakeword_model_paths=jarvis_paths,
    # inference_framework="onnx"
)

# --- ДАЛЕЕ СТАНДАРТНЫЙ КОД ДЛЯ МИКРОФОНА ---

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1280

audio = pyaudio.PyAudio()
mic_stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

print("🎧 Скажите 'Hey Jarvis'...")

try:
    while True:
        # Читаем аудио
        data = np.frombuffer(mic_stream.read(CHUNK), dtype=np.int16)
        
        # Предсказание
        prediction = model.predict(data)
        
        # В v0.4.0 ключи в prediction могут содержать полный путь или имя файла
        # Поэтому проверяем, есть ли сработка по любому ключу, содержащему 'hey_jarvis'
        for key in prediction:
            if "hey_jarvis" in key and prediction[key] > 0.5:
                print(f"🤖 О! Вы меня позвали! (Уверенность: {prediction[key]:.2f})")
                model.reset()

except KeyboardInterrupt:
    print("\nОстановка...")
finally:
    mic_stream.stop_stream()
    mic_stream.close()
    audio.terminate()