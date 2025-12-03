import matplotlib.pyplot
import pygame
import sys
import matplotlib
import time
import csv
import paho.mqtt.client as mqtt
import json
import datetime
 
results = [0.0,0.0,0.0,0.0,0.0,0.0]
            #ph , RPM, temp
set_points = [25.0,10.0,10.0]
pygame.init()
 
BROKER = "1e6503b2032f4e8b9088ae3b04f739e6.s1.eu.hivemq.cloud"
PORT = 8883
TOPIC = "test"

class Button:
    def __init__(self, width, height, text, bg_colour, x, y, text_colour=(255,255,255), font_path=None):
        self.width = width
        self.height = height
        self.text = text
        self.bg_colour = bg_colour
        self.text_colour = text_colour
        self.rect = pygame.Rect(x, y, width, height)
        self.font_path = font_path if font_path else pygame.font.get_default_font()  # fallback font

    def draw(self, screen):
        pygame.draw.rect(screen, self.bg_colour, self.rect, border_radius=8)

        font_size = 10
        font = pygame.font.Font(self.font_path, font_size)
        text_surface = font.render(self.text, True, self.text_colour)

        while text_surface.get_width() < self.rect.width - 10 and text_surface.get_height() < self.rect.height - 10:
            font_size += 1
            font = pygame.font.Font(self.font_path, font_size)
            text_surface = font.render(self.text, True, self.text_colour)

        font_size -= 1
        font = pygame.font.Font(self.font_path, font_size)
        text_surface = font.render(self.text, True, self.text_colour)

        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos) 


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
        global results
        values = payload.split(',')
        ans = []
        for value in range(len(values)):
            if values[value] == "0.0":
                ans.append(results[value])
            else:
                ans.append(values[value])
        results = ans
        return
 
    timestamp = datetime.datetime.now().isoformat(timespec='seconds')
    print(f"[{timestamp}] {data}")

def publish(client,set_points):
    Topic1 = "Targets"
    msg = ",".join([str(val) for val in set_points])
    result = client.publish(Topic1, msg)
    # result: [0, 1]
    status = result[0]
    if status == 0:
        print(f"Send `{msg}` to topic `{Topic1}`")
    else:
        print(f"Failed to send message to topic {Topic1}")


# Create client using new API
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
 
client.tls_set()
 
client.on_connect = on_connect
client.on_message = on_message
 
print("Connecting to broker...")
client.username_pw_set("hivemq.webclient.1764155961822", "3Vt%0E$2K.u9Wd!GvoQc")
client.connect(BROKER, PORT)
 
client.loop_start()
 
# Screen Setup
screen_width = 800
screen_height = 800
 
try:
    screen = pygame.display.set_mode((screen_width, screen_height),pygame.RESIZABLE)
except pygame.error:
    print("Failed to set display mode.")
    sys.exit(1)
pygame.display.set_caption("BioReactor")
 
 
class Graph():
    def __init__(self,xpoints,ypoints,vpoints,xlabels,ylabels,vlabels,graph_name,min_value,max_value):
        self.xpoints = xpoints
        self.ypoints = ypoints
        self.vpoints = vpoints
        self.graph_name = graph_name
        self.xlabels = xlabels
        self.ylabels = ylabels
        self.vlabels = vlabels
        self.max_points = 50
        self.min_value = min_value
        self.max_value = max_value
 
    def create_graph(self):
        matplotlib.pyplot.clf()
        matplotlib.pyplot.plot(self.ypoints, "r-",label = self.ylabels)
        matplotlib.pyplot.xlabel(self.xlabels)
        matplotlib.pyplot.legend()
        matplotlib.pyplot.savefig(self.graph_name, dpi = 500, bbox_inches = "tight")
        
   
    def add_new_value(self,xpoint,ypoint,vpoint):
        if len(self.xpoints) < self.max_points:
            self.xpoints.append(xpoint)
            self.ypoints.append(ypoint)
            self.vpoints.append(vpoint)
            return
        self.xpoints = self.xpoints[1:] + [xpoint]
        self.ypoints = self.ypoints[1:] + [ypoint]
        self.vpoints = self.vpoints[1:] + [vpoint]
        return
   
    def check_in_range(self):
        if self.min_value > self.ypoints[-1]:
            return "INCREASE"
        elif self.max_value < self.ypoints[-1]:
            return "DECREASE"
        else:
            return "NONE"
 
    def draw_graph(self,position):
        graph=pygame.image.load(self.graph_name).convert_alpha()
        graph=pygame.transform.scale(graph,(screen_width//2,screen_height//2))
        screen.blit(graph, position)
 
run = True
ph_graph = Graph([],[],[],"Time(seconds)","pH Level","Voltage Level","bioreactor_images/pH_Graph.png",10,100)
 
motor_graph = Graph([],[],[],"Time(seconds)","RPM","Voltage Level","bioreactor_images/motor_Graph.png",10,100)
 
heating_graph = Graph([],[],[],"Time(seconds)","Temperature (Degrees)","Voltage Level","bioreactor_images/heater_Graph.png",10,100)
 
def receive_inputs():
    global results
    return float(results[0]),float(results[1]), float(results[2]), float(results[3]),  float(results[4]),  float(results[5])    
 
 
total_data = []
 
pH_increase = Button(150,50,"INCREASE pH",(0,255,0),screen_width//2 + 25, screen_height//2 + 25, (255,255,255),None)
pH_decrease = Button(150,50,"DECREASE pH",(255,0,0),screen_width//2 + 225, screen_height//2 + 25, (255,255,255),None)
RPM_increase = Button(150,50,"INCREASE SPEED",(0,255,0),screen_width//2 + 25, screen_height//2 + 130, (255,255,255),None)
RPM_decrease = Button(150,50,"DECREASE SPEED",(255,0,0),screen_width//2 + 225, screen_height//2 + 130, (255,255,255),None)
Temperature_increase = Button(150,50,"INCREASE TEMP",(0,255,0),screen_width//2 + 25, screen_height//2 + 235, (255,255,255),None)
Temperature_decrease = Button(150,50,"DECREASE TEMP",(255,0,0),screen_width//2 + 225, screen_height//2 + 235, (255,255,255),None)

current_font = pygame.font.SysFont("Arial",20)
publish(client, set_points)
curr_time = 0
while run == True:
    flag = False
    screen.fill((0,0,0))
    pygame.time.delay(1000)
    current_text_surface = current_font.render(f"pH: {results[0]} RPM: {results[1]} Temp: {results[2]}", True, (255,255,255))
    screen.blit(current_text_surface,(screen_width//2+10,screen_height//2 + 315))
    current_text_surface = current_font.render(f"pH Voltage: {results[3]} Motor Voltage: {results[4]} Heating Voltage: {results[5]}", True, (255,255,255))
    screen.blit(current_text_surface,(screen_width//2+10,screen_height//2 + 340))
    current_text_surface = current_font.render(f"pH Target: {set_points[0]} Motor Target: {set_points[1]} Heating Target: {set_points[2]}", True, (255,255,255))
    screen.blit(current_text_surface,(screen_width//2+10,screen_height//2 + 370))
    pH_increase.draw(screen)
    pH_decrease.draw(screen)
    RPM_increase.draw(screen)
    RPM_decrease.draw(screen)
    Temperature_increase.draw(screen)
    Temperature_decrease.draw(screen)
    
    for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if pH_increase.is_clicked(event.pos):
                    flag = True
                    set_points[0] += 0.1
                elif pH_decrease.is_clicked(event.pos):
                    flag = True
                    set_points[0] -= 0.1
                elif RPM_increase.is_clicked(event.pos):
                    flag = True
                    set_points[1] += 2
                elif RPM_decrease.is_clicked(event.pos):
                    flag = True
                    set_points[1] -= 2
                elif Temperature_increase.is_clicked(event.pos):
                    flag = True
                    set_points[2] += 1
                elif Temperature_decrease.is_clicked(event.pos):
                    flag = True
                    set_points[2] -= 1
    if flag == True:
        publish(client, set_points)

    ph_value, motor_value, heating_value, ph_voltage, motor_voltage, heating_voltage = receive_inputs()
    total_data.append([curr_time,ph_value,motor_value,heating_value,ph_voltage,motor_voltage,heating_voltage])
    
    ph_graph.add_new_value(curr_time,ph_value,ph_voltage)
    ph_graph.create_graph()
    ph_graph.draw_graph((0,0))
 
    motor_graph.add_new_value(curr_time,motor_value,motor_voltage)
    motor_graph.create_graph()
    motor_graph.draw_graph((screen_width//2,0))
 
    heating_graph.add_new_value(curr_time,heating_value,heating_voltage)
    heating_graph.create_graph()
    heating_graph.draw_graph((0,screen_height//2))
    curr_time += 1
    pygame.display.flip()
 
with open("BioReactor/bioreactor_data.csv","w",newline = "") as f:
    writer = csv.writer(f)
    headers = ["Current Time, pH Value, Motor Value, Heating Value, pH Voltage, Motor Voltage, Heating Voltage"]
    for data in total_data:
        writer.writerow(data)