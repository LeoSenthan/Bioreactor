import paho.mqtt.client as mqtt
import json
import datetime
import sys

BROKER = "engf0001.cs.ucl.ac.uk"
PORT = 1883
TOPIC = "bioreactor_sim/single_fault/telemetry/summary"
MODEL_FILE = "model.json"

# Load trained model
try:
    with open(MODEL_FILE, "r") as f:
        model = json.load(f)
    print(f"Loaded model from {MODEL_FILE}")
except FileNotFoundError:
    print(f"Error: {MODEL_FILE} not found. Please run train_model.py first.")
    sys.exit(1)

# Fault counters
fault_counts = {"temperature_C": 0, "pH": 0, "rpm": 0}


def flatten_dict(d, parent_key="", sep="."):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


# ---------------------------
# Updated callbacks
# ---------------------------


def on_connect(client, userdata, flags, rc, properties=None):
    print("Connected with result code:", rc)
    client.subscribe(TOPIC)
    print(f"Subscribed to: {TOPIC}")


def on_message(client, userdata, message):
    payload = message.payload.decode()
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        print("Non-JSON message:", payload)
        return

    timestamp = datetime.datetime.now().isoformat(timespec="seconds")

    # Flatten data to access "temperature_C.mean" etc easily
    flat_data = flatten_dict(data)

    # Metrics to monitor (mapping setpoint name -> measured key)
    monitored_metrics = {
        "temperature_C": "temperature_C.mean",
        "pH": "pH.mean",
        "rpm": "rpm.mean",
    }

    current_faults = []

    for setpoint, metric_key in monitored_metrics.items():
        if metric_key in flat_data and metric_key in model:
            val = flat_data[metric_key]

            trained_mean = model[metric_key]["mean"]
            trained_stdev = model[metric_key]["stdev"]

            # Check if value is > 3 standard deviations from mean
            # If stdev is 0, any deviation is a fault (unless val == mean)
            if trained_stdev == 0:
                is_fault = val != trained_mean
            else:
                is_fault = abs(val - trained_mean) > (3 * trained_stdev)

            if is_fault:
                fault_counts[setpoint] += 1
                current_faults.append(
                    f"{setpoint} (val={val:.2f}, mean={trained_mean:.2f}, std={trained_stdev:.2f})"
                )

    # Display status
    print(f"[{timestamp}] Faults detected in this window: {len(current_faults)}")
    if current_faults:
        for fault in current_faults:
            print(f"  ALERT: {fault}")

    print(
        f"  Total Fault Counts: Temp={fault_counts['temperature_C']}, pH={fault_counts['pH']}, RPM={fault_counts['rpm']}"
    )
    print("-" * 60)


# Create client
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

print("Connecting to broker...")
client.connect(BROKER, PORT)

client.loop_forever()
