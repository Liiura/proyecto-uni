import paho.mqtt.client as mqtt
import sqlite3
from sqlite3 import Error

# Variables globales
connectionMode = "MQTT_SSL"  # MQTT_SSL, API, MQTT_NO_SSL
running = True  # Define running para controlar el ciclo

# Función para crear la conexión a SQLite
def create_connection():
    try:
        connection = sqlite3.connect('iotdata.db')
        create_table_if_not_exists(connection)
        return connection
    except Error as e:
        print(f"Error al conectar a SQLite: {e}")
        return None

# Función para crear la tabla si no existe
def create_table_if_not_exists(connection):
    try:
        cursor = connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS temperature_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                temperature REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        connection.commit()
        cursor.close()
    except Error as e:
        print(f"Error creando la tabla: {e}")

# Función para insertar la temperatura en la base de datos
def insert_temperature(connection, temperature):
    try:
        cursor = connection.cursor()
        query = "INSERT INTO temperature_logs (temperature) VALUES (?);"
        cursor.execute(query, (temperature,))
        connection.commit()
        cursor.close()
    except Error as e:
        print(f"Error durante la inserción a SQLite: {e}")

# Función que se ejecuta al conectarse al broker MQTT
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("iot/temperature")

# Función que se ejecuta cuando se recibe un mensaje del tópico
def on_message(client, userdata, msg, callback=None):
    temperature = float(msg.payload.decode('utf-8'))
    print(f"Temperature Received: {msg.topic} {temperature}°C")
    
    # Insertar la temperatura en la base de datos SQLite
    connection = create_connection()
    if connection:
        insert_temperature(connection, temperature)
        connection.close()
    
    # Si se proporciona un callback, llamarlo para actualizar la GUI
    if callback:
        callback(f"MQTT: Received temperature {temperature}°C")

running = True  # Reiniciamos 'running' cuando se inicie una nueva simulación

def main(callback=None):
    global running
    client = mqtt.Client()

    # Configurar el cliente MQTT con o sin SSL
    if connectionMode == "MQTT_SSL":
        client.tls_set(ca_certs = "/etc/mosquitto/certs/mosquitto.crt",
                       certfile="/etc/mosquitto/certs/mosquitto.crt",
                       keyfile="/etc/mosquitto/certs/mosquitto.key")
        client.connect("localhost", 8883, 60)
    else:
        client.connect("localhost", 1883, 60)
    
    client.on_connect = on_connect
    client.on_message = lambda client, userdata, msg: on_message(client, userdata, msg, callback)
    
    client.loop_start()

    try:
        while running:
            pass  # Mantener el hilo activo
    except KeyboardInterrupt:
        print("Interrupted by the user, shutting down.")
    finally:
        client.loop_stop()
        client.disconnect()
if __name__ == "__main__":
    main()

