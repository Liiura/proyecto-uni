from flask import Flask, request, jsonify
import sqlite3
from sqlite3 import Error
import threading

app = Flask(__name__)
message_queue = None  # Cola para enviar mensajes a la interfaz gráfica

# Función para crear la conexión y la tabla si no existe
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

# Función para insertar temperatura en la base de datos
def insert_temperature(connection, temperature):
    try:
        cursor = connection.cursor()
        query = "INSERT INTO temperature_logs (temperature) VALUES (?);"
        cursor.execute(query, (temperature,))
        connection.commit()
        cursor.close()
    except Error as e:
        print(f"Error durante la inserción a SQLite: {e}")

# Ruta de la API para recibir la temperatura
@app.route('/api/temperature', methods=['POST'])
def api_temperature():
    if request.is_json:
        data = request.get_json()
        temperature = data.get('temperature')
        if temperature is not None:
            connection = create_connection()
            if connection:
                insert_temperature(connection, temperature)
                connection.close()

                # Enviar el mensaje a la interfaz gráfica a través de la cola
                if message_queue is not None:
                    message_queue.put(f"API: Received temperature {temperature}°C")

                return jsonify({"message": "Temperatura insertada correctamente"}), 201
            else:
                return jsonify({"message": "Error al conectar con la base de datos"}), 500
        else:
            return jsonify({"message": "Falta el parámetro de temperatura"}), 400
    else:
        return jsonify({"message": "El contenido debe ser JSON"}), 400

def start_api(queue):
    global message_queue
    message_queue = queue  # Guardar la cola de mensajes
    app.run(debug=False, use_reloader=False)

if __name__ == '__main__':
    app.run(debug=True)

