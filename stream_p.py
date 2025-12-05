import paho.mqtt.client as mqtt
import json
import datetime

BROKER = "engf0001.cs.ucl.ac.uk"
PORT = 1883
TOPIC = "bioreactor_sim/single_fault/telemetry/summary"

# ---------------------------
# REQUIRED: Updated callbacks
# ---------------------------


# New signature: on_connect(client, userdata, flags, rc, properties)
def on_connect(client, userdata, flags, rc, properties=None):
    print("Connected with result code:", rc)
    client.subscribe(TOPIC)
    print(f"Subscribed to: {TOPIC}")


# New signature: on_message(client, userdata, message)
def on_message(client, userdata, message):
    payload = message.payload.decode()
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        print("Non-JSON message:", payload)
        return

    timestamp = datetime.datetime.now().isoformat(timespec="seconds")
    print(f"[{timestamp}] {data}")


# Create client using new API
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

client.on_connect = on_connect
client.on_message = on_message

print("Connecting to broker...")
client.connect(BROKER, PORT)

client.loop_forever()
