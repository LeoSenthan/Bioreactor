import paho.mqtt.client as mqtt
import json
import statistics
import signal
import sys

BROKER = "engf0001.cs.ucl.ac.uk"
PORT = 1883
TOPIC = "bioreactor_sim/nofaults/telemetry/summary"
OUTPUT_FILE = "model.json"

# Store historical data for training
history = {}


def flatten_dict(d, parent_key="", sep="."):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def save_model_and_exit(signum, frame):
    print("\nFinalizing training...")
    model = {}
    for key, values in history.items():
        if len(values) > 1:
            model[key] = {
                "mean": statistics.mean(values),
                "stdev": statistics.stdev(values),
                "samples": len(values),
            }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(model, f, indent=2)

    print(f"Model saved to {OUTPUT_FILE}")
    sys.exit(0)


# Register signal handler for clean exit
signal.signal(signal.SIGINT, save_model_and_exit)


def on_connect(client, userdata, flags, rc, properties=None):
    print("Connected with result code:", rc)
    client.subscribe(TOPIC)
    print(f"Subscribed to: {TOPIC}")
    print("Collecting data... Press Ctrl+C to save model and exit.")


def on_message(client, userdata, message):
    try:
        payload = message.payload.decode()
        data = json.loads(payload)
        flat_data = flatten_dict(data)

        for key, value in flat_data.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                if key.startswith("window") or key.startswith("faults"):
                    continue

                if key not in history:
                    history[key] = []
                history[key].append(value)

        print(
            f"\rSamples collected: {max(len(v) for v in history.values()) if history else 0}",
            end="",
            flush=True,
        )

    except Exception as e:
        print(f"\nError processing message: {e}")


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

print("Connecting to broker...")
client.connect(BROKER, PORT)
client.loop_forever()
