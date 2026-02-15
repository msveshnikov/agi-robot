from arduino.app_utils import App
from arduino.app_utils import Bridge
from datetime import datetime, UTC
from backend_client import BackendClient
from arduino.app_peripherals.microphone import Microphone
import urllib.request
import urllib.parse
import os
import logging
import io
import base64
import json
import time
import colorsys
import wave
import socketio
import threading


class CameraForwarder:
    def __init__(self, local_url, remote_url):
        self.local_sio = socketio.Client(logger=False, engineio_logger=False)
        self.remote_sio = socketio.Client(logger=False, engineio_logger=False)
        self.local_url = local_url
        self.remote_url = remote_url
        self.last_frame_time = 0
        self.frame_interval = 0.1  # ~10 FPS limit

    def start(self):
        @self.local_sio.event
        def connect():
            logger.info(
                f"CameraForwarder: Connected to local camera at {self.local_url}"
            )

        @self.local_sio.event
        def disconnect():
            logger.info(f"CameraForwarder: Disconnected from local camera")

        @self.remote_sio.event
        def connect():
            logger.info(
                f"CameraForwarder: Connected to remote backend at {self.remote_url}"
            )

        @self.remote_sio.event
        def disconnect():
            logger.info(f"CameraForwarder: Disconnected from remote backend")

        @self.local_sio.on("image")
        def on_image(data):
            current_time = time.time()
            if current_time - self.last_frame_time >= self.frame_interval:
                if self.remote_sio.connected:
                    self.remote_sio.emit("camera", data)
                    self.last_frame_time = current_time

        def _connect_loop():
            while True:
                try:
                    if not self.remote_sio.connected:
                        try:
                            self.remote_sio.connect(self.remote_url)
                        except Exception:
                            pass
                    if not self.local_sio.connected:
                        try:
                            self.local_sio.connect(self.local_url)
                        except Exception:
                            pass
                    time.sleep(5)
                except Exception as e:
                    time.sleep(5)

        threading.Thread(target=_connect_loop, daemon=True).start()
        logger.info(
            f"CameraForwarder started: Local={self.local_url}, Remote={self.remote_url}"
        )


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("robot.main")

BACKEND_URL = os.environ.get("BACKEND_URL", "https://robot.mvpgen.com")
backend = BackendClient(BACKEND_URL)
camera_forwarder = CameraForwarder(
    local_url="http://172.17.0.1:4912", remote_url=BACKEND_URL
)
camera_forwarder.start()
speed = 45
back = False
left = False
right = False
forward = False
panic = False
agi = False
asi = False
alarm = False
lang = "en"
rgb = "255,0,255"
arm1 = 0
arm2 = 0
goal = "Be helpful assistant to the master human"
plan = ""
subplan = ""
space_map = ""
movement_history = []
memory = ""

# Manual override support
agi_running = False
manual_override_event = threading.Event()
was_manual = False  # Track if we were just in manual mode


def bridge_call(method, *args, **kwargs):
    try:
        return Bridge.call(method, *args, **kwargs)
    except Exception as e:
        logger.warning(f"Bridge call '{method}' failed: {e}")
        return None


def bridge_notify(method, *args, **kwargs):
    try:
        return Bridge.notify(method, *args, **kwargs)
    except Exception as e:
        logger.warning(f"Bridge notify '{method}' failed: {e}")
        return None


def speed_callback(client: object, value: int):
    global speed
    logger.info(f"Speed value updated from cloud: {value}")
    speed = value


def panic_callback(client: object, value: bool):
    global panic
    logger.info(f"Panic value updated from cloud: {value}")
    panic = value
    if value and agi_running:
        manual_override_event.set()


def back_callback(client: object, value: bool):
    global back
    logger.info(f"Back value updated from cloud: {value}")
    back = value
    if value and agi_running:
        manual_override_event.set()


def left_callback(client: object, value: bool):
    global left
    logger.info(f"Left value updated from cloud: {value}")
    left = value
    if value and agi_running:
        manual_override_event.set()


def right_callback(client: object, value: bool):
    global right
    logger.info(f"Right value updated from cloud: {value}")
    right = value
    if value and agi_running:
        manual_override_event.set()


def forward_callback(client: object, value: bool):
    global forward
    logger.info(f"Forward value updated from cloud: {value}")
    forward = value
    if value and agi_running:
        manual_override_event.set()


def agi_callback(client: object, value: bool):
    global agi
    logger.info(
        f"[CALLBACK] AGI value updated from cloud: {value} (was: {agi}, agi_running: {agi_running})"
    )
    agi = value


def asi_callback(client: object, value: bool):
    global asi
    logger.info(f"ASI value updated from cloud: {value}")
    asi = value


def goal_callback(client: object, value: str):
    global goal
    logger.info(f"Goal updated from cloud: {value}")
    goal = value
    speak(f"New goal received: {value}")


def lang_callback(client: object, value: str):
    global lang
    logger.info(f"Language updated from cloud: {value}")
    lang = value
    speak(f"Language changed to {value}")


def arm1_callback(client, value):
    global arm1
    logger.info(f"Arm1 value updated from cloud: {value}")
    arm1 = int(value)
    bridge_call("setArm1", arm1)


def arm2_callback(client, value):
    global arm2
    logger.info(f"Arm2 value updated from cloud: {value}")
    arm2 = int(value)
    bridge_call("setArm2", arm2)


def rgb_callback(client: object, value):
    """Callback function to handle RGB light updates from cloud."""
    global rgb
    try:
        swi = getattr(value, "swi", True)
        if isinstance(swi, str):
            swi = swi.lower() == "true"

        if not swi:
            rgb = "0,0,0"
        else:
            h = float(getattr(value, "hue", 0)) / 360.0
            s = float(getattr(value, "sat", 0)) / 100.0
            v = float(getattr(value, "bri", 100)) / 100.0
            r_float, g_float, b_float = colorsys.hsv_to_rgb(h, s, v)
            rgb = f"{int(r_float * 255)},{int(g_float * 255)},{int(b_float * 255)}"

        logger.info(f"RGB value updated from backend: {rgb}")
        bridge_notify("setRGB", rgb)
    except Exception as e:
        logger.error(f"Error handling RGB update: {e}")


def volume_callback(client: object, value: int):
    """Callback function to handle volume updates from backend."""
    try:
        level = int(value)
        level = max(0, min(100, level))  # Clamp to 0-100
        logger.info(f"Volume updated from backend: {level}%")

        # Call media service to set PulseAudio volume
        payload = json.dumps({"level": level}).encode("utf-8")
        req = urllib.request.Request(
            "http://172.17.0.1:5000/volume",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            resp = response.read().decode("utf-8")
            logger.info(f"Volume set successfully: {resp}")
    except Exception as e:
        logger.error(f"Error setting volume: {e}")


# Rainbow effect for listening mode
rainbow_stop_event = None
rainbow_thread = None


def rainbow_effect(stop_event, interval=0.1):
    """Cycles through rainbow colors on the RGB LED until stop_event is set."""
    hue = 0.0
    while not stop_event.is_set():
        # Convert HSV to RGB (full saturation and brightness)
        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        rgb_string = f"{int(r * 255)},{int(g * 255)},{int(b * 255)}"

        try:
            bridge_notify("setRGB", rgb_string)
        except Exception as e:
            logger.warning(f"Error setting RGB during rainbow: {e}")

        # Increment hue (wrap around at 1.0)
        hue = (hue + 0.02) % 1.0
        time.sleep(interval)


def rainbow_while_listening():
    """Start a background rainbow effect. Returns a stop function to call when done."""
    global rainbow_stop_event, rainbow_thread

    # Stop any existing rainbow
    if rainbow_stop_event and rainbow_thread:
        rainbow_stop_event.set()
        rainbow_thread.join(timeout=1.0)

    # Start new rainbow effect
    rainbow_stop_event = threading.Event()
    rainbow_thread = threading.Thread(
        target=rainbow_effect, args=(rainbow_stop_event,), daemon=True
    )
    rainbow_thread.start()
    logger.info("Rainbow effect started")

    def stop_rainbow():
        global rainbow_stop_event, rainbow_thread
        if rainbow_stop_event:
            rainbow_stop_event.set()
            if rainbow_thread:
                rainbow_thread.join(timeout=1.0)
            logger.info("Rainbow effect stopped")
            bridge_notify("setRGB", rgb)

    return stop_rainbow


backend.register("speed", on_write=speed_callback)
backend.register("panic", on_write=panic_callback)
backend.register("back", on_write=back_callback)
backend.register("left", on_write=left_callback)
backend.register("right", on_write=right_callback)
backend.register("forward", on_write=forward_callback)
backend.register("agi", on_write=agi_callback)
backend.register("asi", on_write=asi_callback)
backend.register("goal", on_write=goal_callback)
backend.register("lang", on_write=lang_callback)
backend.register("arm1", on_write=arm1_callback)
backend.register("arm2", on_write=arm2_callback)
backend.register("rgb", on_write=rgb_callback)
backend.register("volume", on_write=volume_callback)
backend.register("distance")
backend.register("temperature")
backend.register("humidity")
backend.register("plan")
backend.register("subplan")
backend.register("space_map")
backend.register("movement_history")
backend.register("memory")
backend.register("alarm")


def play_sound(filename):
    try:
        query = urllib.parse.urlencode({"filename": filename})
        url = f"http://172.17.0.1:5000/play?{query}"
        with urllib.request.urlopen(url, timeout=55) as response:
            logger.info(f"Sound service called: {response.read().decode()}")
    except Exception as e:
        logger.warning(f"Could not call sound service: {e}")


def play_random_sound():
    try:
        url = f"http://172.17.0.1:5000/play_random"
        with urllib.request.urlopen(url, timeout=55) as response:
            logger.info(f"Random sound service called: {response.read().decode()}")
    except Exception as e:
        logger.warning(f"Could not call random sound service: {e}")


def speak(text):
    if lang == "disabled":
        return
    try:
        query = urllib.parse.urlencode({"text": text, "lang": lang})
        url = f"http://172.17.0.1:5000/speak?{query}"
        with urllib.request.urlopen(url, timeout=55) as response:
            audio_data = response.read()
            logger.info(
                f"Speak service called, received {len(audio_data)} bytes of audio"
            )

            # Broadcast speech audio to client browsers via CameraForwarder's remote socket
            if camera_forwarder.remote_sio.connected:
                # Send as base64 encoded string for easier transit over JSON
                audio_b64 = base64.b64encode(audio_data).decode("utf-8")
                camera_forwarder.remote_sio.emit(
                    "speech", {"audio": audio_b64, "text": text, "lang": lang}
                )
                logger.info("Speech broadcasted to backend")
    except Exception as e:
        logger.warning(f"Could not call speak service or broadcast speech: {e}")


def set_distance(d):
    backend.distance = int(d)


def set_temperature(t):
    backend.temperature = t


def set_humidity(h):
    backend.humidity = h


Bridge.provide("set_temperature", set_temperature)
Bridge.provide("set_humidity", set_humidity)
Bridge.provide("set_distance", set_distance)
Bridge.provide("play_random_sound", play_random_sound)

play_sound("/home/arduino/ArduinoApps/robot/python/sounds/startup.wav")
speak("Robot is ready")


def ask_llm_vision(
    distance: float,
    temperature: float = None,
    humidity: float = None,
    plan: str = "",
    subplan: str = "",
    movement_history: list = None,
    space_map: str = "",
    memory: str = "",
    arm1: int = 0,
    arm2: int = 0,
) -> dict:
    """Call the /llm_vision endpoint, sending distance, plan, subplan, space_map, and audio if available. Returns parsed JSON dict or {}."""
    try:
        if movement_history is None:
            movement_history = []
        payload = {
            "distance": distance,
            "temperature": temperature,
            "humidity": humidity,
            "goal": goal,
            "plan": plan,
            "subplan": subplan,
            "space_map": space_map,
            "memory": memory,
            "movement_history": movement_history,
            "lang": lang,
            "asi": asi,
            "arm1": arm1,
            "arm2": arm2,
        }

        # Include mic.wav if it exists
        if os.path.exists("mic.wav"):
            try:
                with open("mic.wav", "rb") as audio_file:
                    audio_data = audio_file.read()
                    audio_base64 = base64.b64encode(audio_data).decode("utf-8")
                    payload["audio"] = audio_base64
                    payload["audio_format"] = "wav"
                    logger.info("Including mic.wav in llm_vision request")
                # Delete the file after reading it
                os.remove("mic.wav")
                logger.info("Deleted mic.wav after inclusion in payload")
            except Exception as audio_err:
                logger.warning(f"Could not read/delete mic.wav: {audio_err}")

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"http://172.17.0.1:5000/llm_vision",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=55) as response:
            resp = response.read().decode("utf-8")
            try:
                return json.loads(resp)
            except Exception:
                logger.warning("llm_vision returned non-json, raw: %s", resp)
                return {}
    except Exception as e:
        logger.warning(f"Could not call LLM vision service: {e}")
        return {}


MEMORY_FILE = "memory.txt"


def load_memory():
    global memory
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                memory = f.read()
            logger.info("Memory loaded from %s", MEMORY_FILE)
        except Exception as e:
            logger.warning("Could not load memory: %s", e)


def save_memory(new_memory):
    global memory
    memory = new_memory
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            f.write(memory)
        logger.info("Memory saved to %s", MEMORY_FILE)
    except Exception as e:
        logger.warning("Could not save memory: %s", e)


load_memory()


def agi_loop():
    """Sends distance + subplan to LLM-vision, handles JSON response.

    {
      "speak": {"text": "..."},
      "sound": "casual",
      "moves": [{"command": "forward|back|left|right|stop", "distance_cm": integer, "angle_deg": integer}, ...],
      "plan": "updated global strategy",
      "subplan": "updated context string",
      "space_map": "updated map string",
      "memory": "updated memory string",
      "alarm": "alarm message if needed"
    }
    """

    global plan, subplan, space_map, memory, forward, back, left, right, movement_history, rgb, alarm, arm1, arm2, agi_running, manual_override_event

    # Clear any previous override at the start
    manual_override_event.clear()

    try:
        distance = bridge_call("getDistance")
        temperature = getattr(backend, "temperature", None)
        humidity = getattr(backend, "humidity", None)
    except Exception as e:
        logger.warning("%s", e)

    logger.info(
        f"AGI loop called with distance: {distance}, temp: {temperature}, hum: {humidity}, plan: {plan}, memory size: {len(memory)}"
    )

    # Run LLM call in a separate thread so we can interrupt it
    llm_result = [None]  # Use list to share result between threads
    llm_exception = [None]

    def llm_thread():
        try:
            llm_result[0] = ask_llm_vision(
                distance=distance,
                temperature=temperature,
                humidity=humidity,
                plan=plan,
                subplan=subplan,
                movement_history=movement_history,
                space_map=space_map,
                memory=memory,
                arm1=arm1,
                arm2=arm2,
            )
        except Exception as e:
            llm_exception[0] = e

    thread = threading.Thread(target=llm_thread, daemon=True)
    thread.start()

    # Poll for completion or manual override every 0.5 seconds
    while thread.is_alive():
        if manual_override_event.is_set() or not agi:
            logger.info(
                "Manual override or AGI disabled during LLM call, aborting AGI loop"
            )
            # Thread will continue but we'll ignore the result
            return
        thread.join(timeout=0.5)

    # Check if there was an exception
    if llm_exception[0]:
        logger.error(f"LLM call failed: {llm_exception[0]}")
        return

    resp = llm_result[0]
    if not resp:
        return

    # Update state if provided
    try:
        if "plan" in resp and isinstance(resp["plan"], str):
            plan = resp["plan"]
        if "subplan" in resp and isinstance(resp["subplan"], str):
            subplan = resp["subplan"]
        if "space_map" in resp and isinstance(resp["space_map"], str):
            space_map = resp["space_map"]
        if "memory" in resp and isinstance(resp["memory"], str):
            save_memory(resp["memory"])
        if "alarm" in resp:
            alarm = resp["alarm"]
    except Exception:
        pass

    # Handle RGB
    try:
        rgb_val = resp.get("rgb")
        if rgb_val and isinstance(rgb_val, str):
            # Validate format "R,G,B"
            parts = rgb_val.split(",")
            if len(parts) == 3:
                rgb = rgb_val
                logger.info(f"AGI set RGB to: {rgb}")
        bridge_notify("setRGB", rgb)
    except Exception as e:
        logger.warning("Warning handling rgb: %s", e)

    # Handle Arm
    try:
        if "arm1" in resp and resp["arm1"] is not None:
            val = int(resp["arm1"])
            arm1 = val  # Update global variable
            backend.arm1 = val
            bridge_call("setArm1", val)
            logger.info(f"AGI set Arm1 to: {val}")

        if "arm2" in resp and resp["arm2"] is not None:
            val = int(resp["arm2"])
            arm2 = val  # Update global variable
            backend.arm2 = val
            bridge_call("setArm2", val)
            logger.info(f"AGI set Arm2 to: {val}")
    except Exception as e:
        logger.warning("Warning handling arm: %s", e)

    # Handle sound
    try:
        snd = resp.get("sound")
        if snd == "casual":
            play_random_sound()
    except Exception as e:
        logger.warning("Warning handling sound: %s", e)

    # Handle movement: process array of movement commands
    try:
        moves = resp.get("moves")
        if moves and isinstance(moves, list):
            # Process each movement command in sequence
            for idx, mv in enumerate(moves):
                if not isinstance(mv, dict):
                    logger.warning(
                        f"Move command at index {idx} is not a dict, skipping"
                    )
                    continue

                # Expected keys: command (forward|back|left|right), distance_cm, angle_deg
                cmd = mv.get("command")
                mv_distance = mv.get("distance_cm")
                angle = mv.get("angle_deg")
                move_cmd = None

                if cmd in ("forward", "back") and mv_distance is not None:
                    # Format: MOVE|direction|distance_cm|speed
                    move_cmd = f"MOVE|{cmd}|{int(mv_distance)}|{speed}"
                elif cmd in ("left", "right") and angle is not None:
                    # Format: TURN|direction|angle_deg|speed
                    move_cmd = f"TURN|{cmd}|{int(angle)}|{speed}"
                elif cmd == "stop":
                    move_cmd = "STOP"

                # Execute the move command and wait for completion
                if move_cmd:
                    logger.info(f"Executing move {idx + 1}/{len(moves)}: {move_cmd}")
                    movement_history.append(mv)
                    bridge_call("move", move_cmd, True)

                    # Check for manual override after move completes
                    if manual_override_event.is_set() or not agi:
                        logger.info(
                            f"Manual override or AGI disabled after move {idx + 1}, stopping AGI movements"
                        )
                        bridge_call("move", "STOP", True)
                        return

    except Exception as e:
        logger.warning("Warning handling move: %s", e)

    # Handle speaking
    try:
        sp = resp.get("speak")
        if sp and isinstance(sp, dict):
            text = sp.get("text")
            if text and lang != "disabled":
                speak(text)

                # Start rainbow effect while listening
                stop_rainbow = rainbow_while_listening()

                # Record mic with dynamic duration extension based on audio level
                mic = Microphone()
                mic.start()
                try:
                    import numpy as np

                    audio_chunk_iterator = (
                        mic.stream()
                    )  # Returns a numpy array iterator
                    start_time = time.time()
                    max_duration = 15  # Maximum recording duration in seconds
                    min_duration = 3  # Initial recording duration
                    current_max = min_duration
                    last_second_chunks = []

                    # Use wave module to write with header
                    with wave.open("mic.wav", "wb") as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)  # S16_LE is 2 bytes
                        wf.setframerate(16000)

                        for chunk in audio_chunk_iterator:
                            wf.writeframes(chunk.tobytes())
                            elapsed = time.time() - start_time

                            # Keep track of chunks in the last second
                            last_second_chunks.append(chunk)

                            # Check if we've reached the current maximum duration
                            if elapsed >= current_max:
                                # Calculate audio level for the last second
                                if last_second_chunks:
                                    # Combine all chunks from the last second
                                    last_second_audio = np.concatenate(
                                        last_second_chunks
                                    )

                                    # Calculate RMS (Root Mean Square) and convert to dB
                                    rms = np.sqrt(
                                        np.mean(
                                            last_second_audio.astype(np.float32) ** 2
                                        )
                                    )
                                    # Convert to dB (reference: max value for int16)
                                    if rms > 0:
                                        db_level = (
                                            20 * np.log10(rms / 32768.0) + 90
                                        )  # Normalize to ~0-90 dB range
                                    else:
                                        db_level = 0

                                    logger.info(
                                        f"Audio level at {elapsed:.1f}s: {db_level:.1f} dB"
                                    )

                                    # If last second was not silent (>45 dB) and we haven't reached max, extend by 1 second
                                    if db_level > 45 and current_max < max_duration:
                                        current_max += 1
                                        logger.info(
                                            f"Audio detected, extending recording to {current_max} seconds"
                                        )
                                        last_second_chunks = []  # Reset for next second
                                    else:
                                        # Either silent or reached max duration
                                        if db_level <= 45:
                                            logger.info(
                                                "Silence detected, stopping recording"
                                            )
                                        break
                                else:
                                    break

                            # Keep only the last second worth of chunks (approximately)
                            # Assuming chunks are small, keep last ~50 chunks (rough estimate)
                            if len(last_second_chunks) > 50:
                                last_second_chunks.pop(0)

                    logger.info(
                        f"Recording finished after {time.time() - start_time:.1f} seconds and saved to mic.wav"
                    )
                finally:
                    mic.stop()
                    # Stop rainbow effect when recording is done
                    stop_rainbow()

    except Exception as e:
        logger.warning("Warning handling speak: %s", e)

    # Sync variables to Backend
    try:
        backend.plan = plan
        backend.subplan = subplan
        backend.space_map = space_map
        backend.movement_history = json.dumps(movement_history)
        backend.memory = memory
        backend.alarm = alarm
        logger.info("Synced variables to Backend")
    except Exception as e:
        logger.warning(f"Error syncing to cloud: {e}")
    finally:
        # Mark AGI as no longer running
        agi_running = False
        logger.info("AGI loop iteration finished")


def loop():
    global speed, back, left, right, forward, agi, panic, agi_running, manual_override_event, was_manual
    try:
        # Check for manual controls first (highest priority)
        manual_control_active = left or right or forward or back

        # Log state changes for debugging
        current_state = f"agi={agi}, agi_running={agi_running}, manual={manual_control_active}, panic={panic}, was_manual={was_manual}"

        if manual_control_active:
            # If manual control is active and AGI is running, signal override
            if agi_running:
                logger.info(
                    f"[STATE] Manual override detected during AGI mode. {current_state}"
                )
                manual_override_event.set()

            # Execute manual controls (non-blocking)
            if left:
                bridge_call("move", f"TURN|left|20|{speed}", False)
            elif right:
                bridge_call("move", f"TURN|right|20|{speed}", False)
            elif forward:
                bridge_call("move", f"MOVE|forward|20|{speed}", False)
            elif back:
                bridge_call("move", f"MOVE|back|20|{speed}", False)
            was_manual = True

        elif panic:
            # Panic mode (second priority)
            if agi_running:
                logger.info(f"[STATE] Panic mode interrupting AGI. {current_state}")
                manual_override_event.set()
            bridge_call("panic", str(speed))
            was_manual = True

        else:
            # No manual/panic active
            # Always clear the override event when no manual control
            manual_override_event.clear()

            # If we were just in manual mode, send STOP
            if was_manual:
                logger.info(
                    f"[STATE] Manual/Panic mode ended, sending STOP. {current_state}"
                )
                bridge_call("move", "STOP", True)
                was_manual = False

            # Check if we should start AGI
            if agi:
                if not agi_running:
                    logger.info(
                        f"[STATE] AGI requested and not running, starting AGI thread. {current_state}"
                    )
                    agi_running = True
                    manual_override_event.clear()  # Ensure event is clear before starting
                    threading.Thread(target=agi_loop, daemon=True).start()
                    logger.info(
                        f"[STATE] AGI thread started. agi_running={agi_running}"
                    )

        time.sleep(0.1)

    except Exception as e:
        logger.error(f"[ERROR] Error in main loop: {e}")


backend.start()
App.run(user_loop=loop)
