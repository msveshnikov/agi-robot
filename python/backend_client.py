import requests
import logging
import time
import threading

logger = logging.getLogger("robot.backend_client")

class BackendClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.state = {}
        self.callbacks = {}
        self.running = False
        self.poll_thread = None
        self.last_updated = None

    def register(self, var_name, on_write=None):
        """Registers a variable for polling/sync."""
        self.callbacks[var_name] = on_write
        logger.info(f"Registered variable: {var_name}")

    def update_state(self, updates):
        """Push updates to the backend."""
        try:
            url = f"{self.base_url}/api/state"
            response = requests.post(url, json=updates, timeout=5)
            if response.status_code == 200:
                self.state.update(updates)
                return True
            else:
                logger.error(f"Failed to update state: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error updating state: {e}")
            return False

    def fetch_state(self):
        """Fetch current state from backend."""
        try:
            url = f"{self.base_url}/api/state"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to fetch state: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error fetching state: {e}")
            return None

    def start(self, poll_interval=0.5):
        """Starts the polling thread."""
        self.running = True
        self.poll_thread = threading.Thread(target=self._poll_loop, args=(poll_interval,), daemon=True)
        self.poll_thread.start()
        logger.info("BackendClient polling thread started")

    def stop(self):
        """Stops the polling thread."""
        self.running = False
        if self.poll_thread:
            self.poll_thread.join()

    def _poll_loop(self, interval):
        while self.running:
            new_state = self.fetch_state()
            if new_state:
                # Track updated_at to avoid redundant trigger
                updated_at = new_state.get('updated_at')
                if updated_at != self.last_updated:
                    self._process_state_change(new_state)
                    self.last_updated = updated_at
                    self.state = new_state
            time.sleep(interval)

    def _process_state_change(self, new_state):
        """Triggers callbacks for changed variables."""
        for var_name, callback in self.callbacks.items():
            if callback and var_name in new_state:
                new_val = new_state[var_name]
                old_val = self.state.get(var_name)
                
                # Check for change
                if new_val != old_val:
                    try:
                        # Handle special case for rgb (object vs string/dict)
                        if var_name == 'rgb' and isinstance(new_val, dict):
                            # Wrap in a simple class to mimic ArduinoCloud ColoredLight behavior if needed
                            class MockValue:
                                def __init__(self, d):
                                    for k, v in d.items():
                                        setattr(self, k, v)
                            callback(self, MockValue(new_val))
                        else:
                            callback(self, new_val)
                    except Exception as e:
                        logger.error(f"Error in callback for {var_name}: {e}")

    # Compatibility methods to mimic ArduinoCloud properties
    def __getattr__(self, name):
        if name in self.state:
            return self.state[name]
        return None

    def __setattr__(self, name, value):
        if name in ['base_url', 'state', 'callbacks', 'running', 'poll_thread', 'last_updated']:
            super().__setattr__(name, value)
        else:
            # Sync to backend if it's a registered variable
            if name in self.callbacks or name in ['distance', 'temperature', 'humidity', 'plan', 'subplan', 'space_map', 'movement_history', 'memory', 'alarm']:
                self.update_state({name: value})
            else:
                super().__setattr__(name, value)
