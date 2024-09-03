import paho.mqtt.client as mqtt
import mysql.connector
from mysql.connector import Error
connectionMode = "MQTT_SSL" #MQTT_SSL, API, MQTT_NO_SSL
running = True
try:
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='12345678',
        database='iotdata'
    )
except Error as e:
    print(f"Error al conectar a MySQL: {e}")
    connection = None

def insert_temperature(temperature):
    global connection
    try:
        if connection.is_connected():
            cursor = connection.cursor()
            query = "INSERT INTO temperature_logs (temperature) VALUES (%s);"
            temperature_str = str(temperature)
            cursor.execute(query, (temperature_str,))
            connection.commit()
            cursor.close()
        else:
            print("La conexión a la base de datos se perdió. Reintentando...")
            # Reintentar conexión
            connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password='12345678',
                database='iotdata'
            )
            insert_temperature(temperature)  # Intentar insertar nuevamente
    except Error as e:
        print(f"Error durante la inserción a MySQL: {e}")
        # Manejar reconexión aquí si es necesario

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe("iot/temperature")

def on_message(client, userdata, msg):
    temperature = float(msg.payload.decode('utf-8'))
    print(f"Temperature Received: {msg.topic} {temperature}°C")
    insert_temperature(temperature)

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Unexpected MQTT disconnection. Will auto-reconnect")
    else:
        print("Disconnected successfully.")

def main():
    global running
    client = mqtt.Client()
    
    if(connectionMode == "MQTT_SSL"):
        client.tls_set(ca_certs = "/etc/mosquitto/certs/mosquitto.crt",
                       certfile="/etc/mosquitto/certs/mosquitto.crt",
                       keyfile="/etc/mosquitto/certs/mosquitto.key",
                       tls_version=mqtt.ssl.PROTOCOL_TLS)
        client.connect("localhost", 8883, 60)
    else:  
        client.connect("localhost", 1883, 60)
    
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    client.loop_start()

    try:
        while running:
            pass  # Mantener el hilo activo
    except KeyboardInterrupt:
        print("Interrupted by the user, shutting down.")
    finally:
        client.loop_stop()
        client.disconnect()
        if connection is not None and connection.is_connected():
            connection.close()
            print("Database connection closed.")

if __name__ == "__main__":
    main()
