import socketio
import base64
import json
import sys

sio = socketio.Client(logger=False, engineio_logger=False)


@sio.event
def connect():
    print("connected")


@sio.on('image')
def on_frame(data):
    # Debug: show incoming payload summary
    try:
        summary = repr(data)
    except Exception:
        summary = '<unreprable>'
    print(f"received (type={type(data).__name__}): {summary[:500]}")

    # Try to locate base64 string or raw bytes in the payload
    b64 = None

    if isinstance(data, bytes):
        # raw JPEG bytes — save directly
        with open('frame.jpg', 'wb') as f:
            f.write(data)
        print('saved frame.jpg (raw bytes)')
        sio.disconnect()
        return

    if isinstance(data, str):
        b64 = data

    if isinstance(data, dict):
        for key in ('b64', 'image', 'img', 'data', 'payload'):
            v = data.get(key)
            if v:
                b64 = v
                break
        # sometimes nested frames list
        if not b64 and 'frames' in data and data['frames']:
            first = data['frames'][0]
            if isinstance(first, (str, bytes)):
                b64 = first

    if isinstance(data, (list, tuple)) and data:
        # payload might come as list [ ... ] — inspect first elements
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
        # nothing usable found — dump payload for inspection
        try:
            with open('frame_raw.json', 'w') as f:
                json.dump(data, f, default=str)
            print('no image found; payload saved to frame_raw.json')
        except Exception as e:
            print('failed to save raw payload:', e)
        sio.disconnect()
        return

    # If it's a data URI, strip the header
    if isinstance(b64, str) and b64.startswith('data:image'):
        parts = b64.split(',', 1)
        if len(parts) == 2:
            b64 = parts[1]

    # If we somehow have bytes in b64 variable, handle
    if isinstance(b64, bytes):
        with open('frame.jpg', 'wb') as f:
            f.write(b64)
        print('saved frame.jpg (bytes)')
        sio.disconnect()
        return

    # Decode base64 and write
    try:
        img = base64.b64decode(b64)
    except Exception as e:
        print('base64 decode failed:', e)
        with open('frame_raw.txt', 'w') as f:
            f.write(str(b64)[:10000])
        sio.disconnect()
        return

    with open('frame.jpg', 'wb') as f:
        f.write(img)
    print('saved frame.jpg')
    sio.disconnect()


@sio.event
def disconnect():
    print("disconnected")


if __name__ == '__main__':
    # replace with your server URL if different
    try:
        sio.connect('http://192.168.1.33:4912')
        sio.wait()
    except Exception as e:
        print('connect/wait failed:', e)
        sys.exit(1)

