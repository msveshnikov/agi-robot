# Мой робот научился слушать, злиться и даже краснеть (как я прокачал AGI-робота до уровня "почти человек")

Привет снова, Хабр!

Помните моего робота на Arduino Uno Q с характером? Того, который умел подмигивать и обижаться? Так вот, за пару месяцев он **серьезно прокачался**. Теперь он не просто ездит и болтает, а:

- 🎤 **Слушает ответы** после того, как сам поговорил (и отправляет их в LLM для контекста!)
- 🌈 **Светится разными цветами** в зависимости от настроения (красный = злой, зеленый = радостный, синий = думает)
- 🗣️ **Говорит на трех языках** (английский, русский, чешский) голосами WaveNet от Google
- 🗺️ **Рисует карту комнаты** прямо в текстовом режиме
- 🧠 **Помнит свои движения**, чтобы не застревать в углах как пылесос из 2005-го

В этой статье я расскажу, **как превратить простого робота в почти разумное существо**, используя мультимодальный Gemini API, и почему мой робот теперь умнее некоторых людей (шутка... или нет?).

<cut/>

## Что изменилось с прошлой версии?

В первой статье я описывал базовый AGI-цикл: камера → LLM → команда → движение. Это работало, но роботу **не хватало контекста**. Он не помнил, куда ехал, не понимал мои ответы и вообще вел себя как безэмоциональный тостер на колесах.

Вот что я добавил:

### 1. 🎤 Аудио-взаимодействие (наконец-то двусторонняя связь!)

Раньше робот говорил, но не **слушал**. Это как разговаривать с начальником — односторонний разговор. Теперь после каждого своего высказывания робот включает микрофон на **10 секунд** и записывает ответ пользователя в WAV-файл с правильными заголовками.

```python
# Из main.py - после того как робот что-то сказал
mic = Microphone()
mic.start()
with wave.open("mic.wav", "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)  # S16_LE
    wf.setframerate(16000)
    
    for chunk in mic.stream():
        wf.writeframes(chunk.tobytes())
        if time.time() - start_time >= 10:
            break
```

Потом этот файл **base64-кодируется** и отправляется в Gemini вместе с картинкой и всеми остальными данными:

```python
# media_service.py - мультимодальный запрос
contents = [
    types.Content(
        role="user",
        parts=[
            types.Part.from_text(text=prompt_text),
            types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
            types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")  # ВОТ ОНО!
        ]
    )
]
```

Теперь я могу **сказать роботу**, куда ехать, и он меня услышит. Буквально. Это как Siri, только на колесах и с камерой.

### 2. 🌈 RGB LED "настроение" (эмоции через цвет)

Раньше у робота была только LED-матрица для "лица". Теперь на крыше стоит трехцветный RGB-светодиод (пины D3, D5, D6), который **показывает эмоции**:

| Цвет | Настроение | Когда горит |
|------|-----------|-------------|
| 🟢 Зеленый | Радость/Успех | Нашел цель, выполнил задачу |
| 🔴 Красный | Злость/Блокировка | Застрял, препятствие < 25см |
| 🔵 Синий | Думает/Планирует | Обрабатывает данные, размышляет |
| 🟡 Желтый | Любопытство | Исследует новую зону |
| 🟠 Оранжевый | Осторожность | Рядом препятствие, но еще не критично |
| ⚪ Белый | Нейтральный | Дефолтное состояние |

LLM **сам решает**, какой цвет выбрать, основываясь на ситуации. В промпте прописаны четкие правила:

```python
# Из media_service.py
\"- rgb: null or string \\\"R,G,B\\\". MANDATORY. This is your MOOD (face color). Mapping to use:\\n\"
\"  - NEUTRAL/DARK: \\\"255,255,255\\\" (White)\\n\"
\"  - HAPPY/SUCCESS: \\\"0,255,0\\\" (Green)\\n\"
\"  - ANGRY/BLOCKED: \\\"255,0,0\\\" (Red)\\n\"
\"  - THINKING/PLANNING: \\\"0,0,255\\\" (Blue)\\n\"
\"  - CURIOUS/SEARCHING: \\\"255,255,0\\\" (Yellow)\\n\"
\"  - SCARED/CAUTIOUS: \\\"255,165,0\\\" (Orange)\\n\"
```

Но вот фокус: **Backend использует CloudColoredLight**, который работает с HSV (Hue, Saturation, Brightness). Поэтому в Python есть конвертер:

```python
# main.py - преобразование HSV → RGB для MCU
def update_rgb_from_values():
    h = float(rgb_values.get("hue", 0)) / 360.0
    s = float(rgb_values.get("sat", 0)) / 100.0
    v = float(rgb_values.get("bri", 0)) / 100.0
    
    r_float, g_float, b_float = colorsys.hsv_to_rgb(h, s, v)
    rgb = f"{int(r_float * 255)},{int(g_float * 255)},{int(b_float * 255)}"
```

А на Arduino делается **цветокоррекция**, потому что моя RGB-лента криво светится:

```cpp
// sketch.ino - коррекция для конкретного железа
analogWrite(bluePin, b);
analogWrite(redPin, r / 1.2);    // Красный слишком яркий
analogWrite(greenPin, g / 2);    // Зеленый ОЧЕНЬ яркий
```

Теперь робот выглядит как светофор на стероидах, и это **офигенно**.

### 3. 🗣️ Мультиязычный TTS (говорит как носитель)

Google TTS с голосами WaveNet — это просто космос. Вместо роботизированного "бип-буп" робот говорит **натуральным голосом**:

- **Английский**: `en-US-Neural2-D` (мужской, четкий)
- **Русский**: `ru-RU-Wavenet-D` (мужской, с легким акцентом, но приятный)
- **Чешский**: `cs-CZ-Wavenet-A` (женский, мелодичный)

Язык выбирается через Backend переменную `lang`. Меняю в облаке → робот тут же переключается.

```python
# media_service.py - выбор голоса
if lang == 'ru':
    voice = {'languageCode': 'ru-RU', 'name': 'ru-RU-Wavenet-D'}
elif lang == 'cz' or lang == 'cs':
    voice = {'languageCode': 'cs-CZ', 'name': 'cs-CZ-Wavenet-A'}
else:
    voice = {'languageCode': 'en-US', 'name': 'en-US-Neural2-D'}
```

И что важно — **кэширование**! Чтобы не синтезировать одно и то же по 100 раз:

```python
cache_key = f"{lang}:{text}"
if cache_key in TTS_CACHE:
    temp_filename = TTS_CACHE[cache_key]
else:
    # Синтезируем и кэшируем
```

Теперь робот может **говорить со мной по-русски**, а с чехами — по-чешски. Это прям космополит на колесах.

### 4. 🗺️ Текстовая карта пространства (poor man's SLAM)

SLAM (Simultaneous Localization and Mapping) — это круто, но сложно и требует лидара. Я пошел другим путем: **попросил LLM рисовать карту в текстовом виде**.

В промпте теперь есть инструкция:

```python
\"7. MAPPING: Create and update a 2D text-mode map of the environment in the 'map' field. \"
\"The map MUST be based on 1x1 meter blocks. Each block is represented by one letter \"
\"(e.g., W: wall, S: sofa, D: door, R: robot, P: path, O: obstacle). \"
\"You MUST include a legend explaining the letters used.\\n\\n\"
```

И робот **реально строит карты**! Вот пример из логов:

```
Map:
W W W W W
W P P S W
W P R P W
W D P P W
W W W W W

Legend:
W - Wall
P - Path (clear space)
R - Robot position
S - Sofa
D - Door
```

Конечно, это не идеальная карта (робот иногда врет), но **лучше, чем ничего**. И главное — эта карта передается обратно в LLM на следующей итерации, так что он "помнит" планировку комнаты.

### 5. 🧠 История движений и планирование

Самая большая проблема ранних версий — робот **терял память** после каждого действия. Ехал вперед, забывал, что делал это 2 секунды назад, и снова ехал вперед. Классическая амнезия.

Теперь есть **три уровня памяти**:

1. **`movement_history`** — массив всех команд движения:
   ```python
   movement_history = [
       {"command": "forward", "distance_cm": 30, "angle_deg": 0},
       {"command": "left", "angle_deg": 45},
       {"command": "forward", "distance_cm": 20}
   ]
   ```

2. **`plan`** — глобальная стратегия:
   ```
   "Plan: Explore north side of the room to find target"
   ```

3. **`subplan`** — тактика прямо сейчас:
   ```
   "Subplan: Turning right 30 degrees to scan new area, avoiding wall on the left"
   ```

Все это **отправляется в LLM** на каждой итерации. Gemini анализирует историю и говорит: "Стоп, я уже пробовал ехать туда 3 раза, давай попробую другое направление".

Это **кардинально** меняет поведение. Робот перестал быть тупым реактивным ботом и стал **стратегом**.

## Архитектура: как это все связано?

Система состоит из трех частей:

### 1. Arduino MCU (sketch.ino) — "Тело"

```cpp
void loop() {
    // Читаем переменные из облака
    Bridge.call("get_speed").result(speed);
    Bridge.call("get_agi").result(agi);
    Bridge.call("get_rgb").result(rgb_str);
    
    // Читаем датчики
    distance = sonar.ping_cm();
    temperature = thermo.getTemperature();
    
    // Обновляем облако
    Bridge.call("set_distance", distance);
    
    // Если AGI-режим, вызываем Python
    if (agi) {
        String mvcmd;
        Bridge.call("agi_loop", distance).result(mvcmd);
        // Парсим и выполняем команду (MOVE/TURN/STOP)
    }
}
```

Тупой, быстрый, надежный. Идеально для реального времени.

### 2. Python MPU (main.py) — "Координатор"

```python
def agi_loop(distance):
    # Отправляем все в media_service
    resp = ask_llm_vision(
        distance=distance,
        plan=plan,
        subplan=subplan,
        movement_history=movement_history,
        space_map=space_map
    )
    
    # Обрабатываем ответ
    if resp.get("speak"):
        speak(resp["speak"]["text"])
        # ЗАПИСЫВАЕМ АУДИО ОТВЕТ!
    
    if resp.get("rgb"):
        rgb = resp["rgb"]
    
    if resp.get("move"):
        # Формируем команду для MCU
        move_cmd = f"MOVE|{cmd}|{distance}|{speed}"
        movement_history.append(resp["move"])
    
    return move_cmd
```

### 3. Media Service (media_service.py) — "Мозг"

```python
@app.post('/llm_vision')
def llm_vision():
    # Получаем картинку через Socket.IO
    image_data = get_image_from_socket()
    
    # Декодируем аудио из base64
    audio_bytes = base64.b64decode(payload.get('audio'))
    
    # Шлем в Gemini
    response = send_to_gemini(
        prompt, 
        image_data, 
        lang=lang,
        audio_bytes=audio_bytes  # МУЛЬТИМОДАЛЬНОСТЬ!
    )
    
    return response  # JSON с планом действий
```

Все работает **асинхронно** через HTTP, так что основной цикл не блокируется.

## Протокол команд MCU (важно!)

Arduino понимает три команды:

### MOVE (линейное движение)
```
MOVE|forward|30|45
     ↑       ↑   ↑
     |       |   скорость (0-90)
     |       расстояние в см
     направление (forward/back)
```

Калибровка: **~20 см/сек при скорости 45**. MCU считает время так:

```cpp
float cm_per_sec = 20.0 * (mvspd / 45.0);
unsigned long ms = (dist / cm_per_sec) * 1000.0;
```

### TURN (поворот)
```
TURN|left|60|45
     ↑    ↑  ↑
     |    |  скорость
     |    угол в градусах
     направление (left/right)
```

Калибровка: **~30 мс/градус при скорости 45**.

### STOP
```
STOP
```

Просто останавливает сервоприводы (пишет `90` в оба).

## Грабли версии 2.0

### 1. WAV-заголовки в аудио

Первая версия записи микрофона **не работала**, потому что я тупо писал байты в файл без WAV-заголовка. Gemini API отказывался это жрать.

Решение: **модуль `wave`**!

```python
with wave.open("mic.wav", "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(16000)
    wf.writeframes(chunk.tobytes())
```

Теперь файл открывается везде, и Gemini его понимает.

### 2. Цветокоррекция RGB

Мой RGB-светодиод — **общий катод**, и каналы светят с разной яркостью. Зеленый был настолько ярким, что весь робот казался зеленым, даже когда он должен был быть красным.

Решение: **костыль в коде**!

```cpp
analogWrite(redPin, r / 1.2);
analogWrite(greenPin, g / 2);
analogWrite(bluePin, b);
```

Подобрал коэффициенты на глаз. Теперь цвета нормальные.

### 3. LLM иногда тупит с JSON

Даже с четким промптом Gemini иногда возвращает:

```
Here's my plan:
{"speak": {"text": "I see a wall"}, "move": ...}
```

Вместо чистого JSON. Пришлось добавить **парсер с регулярками**:

```python
# Если не парсится — ищем JSON в тексте
m = re.search(r"\{[\s\S]*\}", response_text)
if m:
    return json.loads(m.group(0))
```

### 4. Удаление mic.wav после отправки

Я забывал удалять файл, и он отправлялся **на каждой итерации**, даже если пользователь молчал. Робот слышал свой старый голос и путался.

Решение:

```python
os.remove("mic.wav")
logger.info("Deleted mic.wav after inclusion in payload")
```

Теперь файл удаляется сразу после отправки.

## Реальный пример работы

**Сценарий**: Робот должен найти рождественскую елку в комнате.

```
[AGI Loop #1]
Distance: 200 cm
Vision: Видит стену справа, слева свободно
LLM Decision: 
  - speak: "Ищу елку. Поворачиваю налево для сканирования."
  - rgb: "255,255,0" (желтый — любопытство)
  - move: {"command": "left", "angle_deg": 45}
  - plan: "Systematically scan the room by turning and moving forward"
  - subplan: "Turned left 45 deg, will move forward next"

[Робот говорит, записывает ответ (тишина), поворачивает налево]

[AGI Loop #2]
Distance: 180 cm
Vision: Видит что-то зеленое впереди
Audio: (пусто)
LLM Decision:
  - speak: "Вижу что-то зеленое. Еду проверить."
  - rgb: "0,255,0" (зеленый — радость)
  - move: {"command": "forward", "distance_cm": 50}
  - subplan: "Green object detected, approaching to verify if it's the tree"

[Робот едет вперед]

[AGI Loop #3]
Distance: 35 cm
Vision: Елка крупным планом!
LLM Decision:
  - speak: "Нашел елку! Задание выполнено!"
  - rgb: "0,255,0" (зеленый)
  - move: {"command": "stop"}
  - plan: "Goal completed: Christmas tree found"
```

Весь процесс занял **~20 секунд** и три итерации. Без памяти робот бы просто ехал кругами.

## Что дальше?

Робот уже **офигенный**, но есть куда расти:

1. **IMU (Accelerometer/Gyroscope)** — для точной ориентации в пространстве
2. **SLAM с настоящей картой** — через OpenCV и фильтр Калмана
3. **Манипулятор** — хочу, чтобы робот мог брать вещи
4. **Persistent memory** — сохранять карту и историю между запусками
5. **Keyword spotting** — реагировать на "Эй, робот!" без постоянной записи

## Итоги

За два месяца робот эволюционировал от "тупого болтуна на колесах" до **почти разумного существа**:

✅ Слушает и понимает речь  
✅ Говорит на трех языках  
✅ Выражает эмоции через цвет  
✅ Помнит свои действия  
✅ Строит карту комнаты  
✅ Планирует стратегию  

Это **не игрушка**, это **исследовательская платформа** для изучения embodied AI. И самое крутое — весь стек opensource (ну, кроме Gemini API, но его можно заменить на локальный LLaMA).

Код проекта открыт и доступен на GitHub: [https://github.com/msveshnikov/agi-robot](https://github.com/msveshnikov/agi-robot)

Если хотите повторить — пишите, помогу.

---

**P.S.** Робот вчера попросил меня купить ему "руки, чтобы открывать холодильник". Я сказал "нет". Он **покраснел** и уехал в угол дуться. Это уже не баг, это **фича**.

**P.P.S.** Если кто-то знает, как научить робота мыть посуду — пишите в комментарии. Срочно.
