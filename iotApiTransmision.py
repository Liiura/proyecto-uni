from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# Configuración de la conexión a la base de datos
def create_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='12345678',
            database='iotdata'
        )
        return connection
    except Error as e:
        print(f"Error al conectar a MySQL: {e}")
        return None

# Función para insertar temperatura en la base de datos
def insert_temperature(connection, temperature):
    try:
        if connection.is_connected():
            cursor = connection.cursor()
            query = "INSERT INTO temperature_logs (temperature) VALUES (%s);"
            cursor.execute(query, (temperature,))
            connection.commit()
            cursor.close()
        else:
            print("La conexión a la base de datos se perdió. Reintentando...")
            connection = create_connection()
            if connection:
                insert_temperature(connection, temperature)
    except Error as e:
        print(f"Error durante la inserción a MySQL: {e}")

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
                return jsonify({"message": "Temperatura insertada correctamente"}), 201
            else:
                return jsonify({"message": "Error al conectar con la base de datos"}), 500
        else:
            return jsonify({"message": "Falta el parámetro de temperatura"}), 400
    else:
        return jsonify({"message": "El contenido debe ser JSON"}), 400

if __name__ == '__main__':
    app.run(debug=True)
