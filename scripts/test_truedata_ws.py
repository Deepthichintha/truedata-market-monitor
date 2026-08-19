import json
import os
import time

import websocket
from dotenv import load_dotenv

load_dotenv()

username = os.getenv("TRUEDATA_USERNAME")
password = os.getenv("TRUEDATA_PASSWORD")

if not username or not password:
    raise RuntimeError("TrueData credentials are missing from .env")

url = (
    "wss://push.truedata.in:8086"
    f"?user={username}&password={password}"
)

print("Connecting to TrueData sandbox WebSocket...")

ws = websocket.create_connection(
    url,
    timeout=15,
)

print("Connected successfully.")

try:
    # Subscribe to ONE symbol first.
    request = {
        "method": "addsymbol",
        "symbols": ["AARTIIND"],
    }

    print("Subscribing to AARTIIND...")
    ws.send(json.dumps(request))

    # Receive messages for 30 seconds.
    start_time = time.time()

    while time.time() - start_time < 30:
        message = ws.recv()

        print("\n--- MESSAGE ---")
        print(message)

except KeyboardInterrupt:
    print("\nStopping...")

finally:
    try:
        ws.send(json.dumps({"method": "logout"}))
    except Exception:
        pass

    ws.close()
    print("Disconnected.")
