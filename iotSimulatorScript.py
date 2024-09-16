import paho.mqtt.client as mqtt
import random
import time
import requests
import json

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")

connectionMode = "MQTT_NO_SSL"  # MQTT_SSL, API, MQTT_NO_SSL
running = True  # Añadir esto para poder detener la simulación

def send_temperature(temperature):
    url = 'http://127.0.0.1:5000/api/temperature'
    headers = {'Content-Type': 'application/json'}
    data = {
        'temperature': temperature
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    if response.status_code == 201:
        print("Temperatura enviada correctamente.")
    else:
        print(f"Error al enviar temperatura: {response.status_code}, {response.json()}")

running = True  # Inicializamos la variable 'running'

def main():
    global running
    client = mqtt.Client()
    if(connectionMode != "API"):
        if(connectionMode == "MQTT_SSL"):
            client.tls_set(ca_certs="/etc/mosquitto/certs/mosquitto.crt",
                           certfile="/etc/mosquitto/certs/mosquitto.crt",
                           keyfile="/etc/mosquitto/certs/mosquitto.key",
                           tls_version=mqtt.ssl.PROTOCOL_TLS)
            client.connect("localhost", 8883, 60)
        else:
            client.connect("localhost", 1883, 60)
        
        client.loop_start()

    try:
        while running:
            temperatura = random.uniform(10, 30)
            if connectionMode == "API":
                send_temperature(temperatura)
            else:
                client.publish("iot/temperature", f"{temperatura:.2f}")
            time.sleep(3)
    except KeyboardInterrupt:
        print("Simulación terminada por el usuario.")
    finally:
        client.loop_stop()
        client.disconnect()
if __name__ == "__main__":
    main()
