import paho.mqtt.client as mqtt
import mysql.connector
from mysql.connector import Error
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from base64 import urlsafe_b64encode, urlsafe_b64decode
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
import os

def encrypt_message(message, password):
    # Genera una clave a partir de la contraseña
    salt = os.urandom(16)  # Guardar este salt para usar en descifrado
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    key = kdf.derive(password.encode())

    # Genera el IV y lo almacena para su uso en el descifrado
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(message.encode()) + padder.finalize()
    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
    # Devuelve el IV junto con los datos cifrados, todo codificado en base64
    return urlsafe_b64encode(iv + encrypted_data)

def decrypt_message(encrypted_message, password):
    encrypted_message = urlsafe_b64decode(encrypted_message)
    iv = encrypted_message[:16]
    encrypted_message = encrypted_message[16:]

    # Genera la misma clave a partir de la contraseña y el salt guardado
    # Aquí deberás tener acceso al mismo salt usado durante el cifrado
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,  # El salt debe ser el mismo que se usó para cifrar
        iterations=100000,
        backend=default_backend()
    )
    key = kdf.derive(password.encode())

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    padded_data = decryptor.update(encrypted_message) + decryptor.finalize()
    return unpadder.update(padded_data) + unpadder.finalize()

# Ejemplo de uso
salt = os.urandom(16)  # Guardar este salt para usar en descifrado
password = '8eb30734-b139-4779-a671-d53d48f82842'
try:
    connection = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
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
            # cursor.execute(query, (temperature,))
            temperature_str = str(temperature)
            # encrypted = encrypt_message(temperature_str, password)
            # print(encrypted)
            cursor.execute(query, (temperature_str,))
            connection.commit()
            cursor.close()
        else:
            print("La conexión a la base de datos se perdió. Reintentando...")
            # Reintentar conexión
            connection = mysql.connector.connect(
                host='localhost',
                user='root',
                password='',
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
if __name__ == "__main__":
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    client.connect("localhost", 1883, 60)
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("Interrupted by the user, shutting down.")
        client.disconnect()
        if connection is not None and connection.is_connected():
            connection.close()
            print("Database connection closed.")
