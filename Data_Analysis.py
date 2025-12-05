import paho.mqtt.client as mqtt
import json
import datetime
BROKER = "engf0001.cs.ucl.ac.uk"
PORT = 1883
TOPIC = "bioreactor_sim/nofaults/telemetry/summary"
 
# ---------------------------
# REQUIRED: Updated callbacks
# ---------------------------
temperature_data = [] 
rpm_data = []
ph_data = []
setpoints = []
# New signature: on_connect(client, userdata, flags, rc, properties)
def on_connect(client, userdata, flags, rc, properties=None):
    print("Connected with result code:", rc)
    client.subscribe(TOPIC)
    print(f"Subscribed to: {TOPIC}")
    
count = 1
# New signature: on_message(client, userdata, message)
def on_message(client, userdata, message):
    global count
    payload = message.payload.decode()
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return
    if count > -1:
            temperature_data.append(data["temperature_C"])
            ph_data.append(data["pH"])
            rpm_data.append(data["rpm"])
            setpoints.append(data["setpoints"])
            print(temperature_data)
            print(rpm_data)
            print(ph_data)
            print(setpoints)
            count -= 1
 
# Create client using new API
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
 
client.on_connect = on_connect
client.on_message = on_message
 
print("Connecting to broker...")
client.connect(BROKER, PORT)
 
client.loop_forever()