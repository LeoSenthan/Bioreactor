import paho.mqtt.client as mqtt
import json
from collections import deque
import statistics

# --- MQTT settings ---
BROKER = "engf0001.cs.ucl.ac.uk"
PORT = 1883
TOPIC = "bioreactor_sim/single_fault/telemetry/summary"

WINDOW_SIZE = 50      # Sliding window for baseline
PERSISTENCE = 3       # Number of consecutive anomalies required
K = 3                 # Threshold multiplier for std deviation
TOLERANCE = {
    "temperature": 0.5,  # ignore deviations within ±0.5°C
    "pH": 0.1,           # ignore deviations within ±0.1 pH
    "rpm": 10            # ignore deviations within ±10 rpm
}

VARIABLE_TO_FAULT = {
    'temperature': 'therm_voltage_bias',
    'pH': 'ph_sensor_fault',
    'rpm': 'motor_sensor_fault'
}

window_means = deque(maxlen=WINDOW_SIZE)
persistence_counter = {"temperature": 0, "pH": 0, "rpm": 0}
data_list = []

def robust_mean_std(values):
    if not values:
        return 0, 0
    median = statistics.median(values)
    mad = statistics.median([abs(x - median) for x in values])
    # Approximate std from MAD
    std = 1.4826 * mad if mad > 0 else 0.0001
    return median, std

def detect_anomalies(curr_vals, window_vals):
    anomalies = []
    medians, stds = [], []

    for i, var in enumerate(["temperature", "pH", "rpm"]):
        col = [v[i] for v in window_vals]
        median, std = robust_mean_std(col)
        medians.append(median)
        stds.append(std)

        # Check if outside K*std and setpoint tolerance
        if abs(curr_vals[i] - median) > max(K*std, TOLERANCE[var]):
            persistence_counter[var] += 1
        else:
            persistence_counter[var] = 0

        # Flag only if persistence reached
        if persistence_counter[var] >= PERSISTENCE:
            anomalies.append(var)

    return anomalies

def handle_error_detection(data):
    temp = data["temperature_C"]["mean"]
    ph = data["pH"]["mean"]
    rpm = data["rpm"]["mean"]

    curr_vals = [temp, ph, rpm]
    window_means.append(curr_vals)

    if len(window_means) < 10:
        # Not enough data for robust detection
        feature_vector = curr_vals + [data.get("faults", {})]
        data_list.append(feature_vector)
        print("Feature vector:", feature_vector)
        return

    anomalies = detect_anomalies(curr_vals, window_means)

    # Compare with last_active faults
    last_active = data.get("faults", {}).get("last_active", [])
    matched_faults = []
    for anomaly in anomalies:
        expected_fault = VARIABLE_TO_FAULT.get(anomaly)
        for fault in last_active:
            if fault.get("name") == expected_fault and fault.get("counts", 0) >= 5:
                matched_faults.append(anomaly)

    val = curr_vals + [data.get("faults", {})]
    data_list.append(val)

    # Print results
    if anomalies:
        print("Anomaly detected in:", ", ".join(anomalies))
        if matched_faults:
            print("Matches last_active fault(s):", ", ".join(matched_faults))
        else:
            print("No matching last_active faults.")
    else:
        if matched_faults:
            print("ERROR: false positive detected")

def on_connect(client, userdata, flags, rc, properties=None):
    print("Connected with result code:", rc)
    client.subscribe(TOPIC)
    print(f"Subscribed to: {TOPIC}")

def on_message(client, userdata, message):
    payload = message.payload.decode()
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        print("Non-JSON message received:", payload)
        return
    handle_error_detection(data)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

print("Connecting to broker...")
client.connect(BROKER, PORT)
client.loop_forever()
