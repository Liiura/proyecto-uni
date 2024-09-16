import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import threading
import iotSimulatorScript
import iotSubscriberNoCrypto
import iotApiTransmision
import queue  # Importamos Queue para comunicar la API con la GUI

class IoTApp:
    def __init__(self, root):
        self.root = root
        self.root.title("IoT Simulator Control Panel")
        self.root.geometry("400x400")  
        self.root.resizable(False, False)

        self.style = ttk.Style()
        self.style.configure("TButton", font=("Arial", 10))
        self.style.configure("TLabel", font=("Arial", 12))
        self.style.configure("TRadiobutton", font=("Arial", 10))

        self.connection_mode = tk.StringVar(value=iotSimulatorScript.connectionMode)

        # Frame for Mode Selection
        mode_frame = ttk.LabelFrame(root, text="Connection Mode", padding=(20, 10))
        mode_frame.pack(pady=20, padx=20, fill="both", expand="yes")

        ttk.Radiobutton(mode_frame, text="MQTT without SSL", variable=self.connection_mode, value="MQTT_NO_SSL").pack(anchor=tk.W, pady=5)
        ttk.Radiobutton(mode_frame, text="MQTT with SSL", variable=self.connection_mode, value="MQTT_SSL").pack(anchor=tk.W, pady=5)
        ttk.Radiobutton(mode_frame, text="API HTTP", variable=self.connection_mode, value="API").pack(anchor=tk.W, pady=5)

        # Frame for Control Buttons
        control_frame = ttk.Frame(root, padding=(20, 10))
        control_frame.pack(pady=20)

        start_button = ttk.Button(control_frame, text="Start Simulation", command=self.start_simulation)
        start_button.pack(side=tk.LEFT, padx=10)

        stop_button = ttk.Button(control_frame, text="Stop Simulation", command=self.stop_simulation)
        stop_button.pack(side=tk.LEFT, padx=10)

        self.simulation_running = False
        self.subscriber_thread = None

        # Variable para indicar si la API ya está corriendo
        self.api_running = False

        # Cola para recibir mensajes de la API
        self.message_queue = queue.Queue()

        # Caja de texto para mostrar los mensajes recibidos
        self.messages_textbox = tk.Text(root, height=10, width=50)
        self.messages_textbox.pack(pady=20)

        # Loop para procesar mensajes de la cola
        self.root.after(100, self.process_queue)

    def process_queue(self):
        while not self.message_queue.empty():
            message = self.message_queue.get()
            self.display_message(message)
        self.root.after(100, self.process_queue)

    def start_simulation(self):
        if self.simulation_running:
            messagebox.showwarning("Warning", "Simulation is already running.")
            return

        # Reiniciar la variable 'running' en ambos módulos antes de iniciar la simulación
        iotSimulatorScript.running = True
        iotSubscriberNoCrypto.running = True

        iotSimulatorScript.connectionMode = self.connection_mode.get()
        iotSubscriberNoCrypto.connectionMode = self.connection_mode.get()

        # Verificar si la API ya está corriendo antes de intentar iniciarla
        if not self.api_running:
            api_thread = threading.Thread(target=iotApiTransmision.start_api, args=(self.message_queue,))
            api_thread.daemon = True
            api_thread.start()
            self.api_running = True  # Marcamos que la API ya está corriendo

        # Mostrar mensajes basados en el modo de conexión
        if iotSimulatorScript.connectionMode == "MQTT_NO_SSL":
            messagebox.showinfo("Information", "The data will be transmitted in plain text.")
        elif iotSimulatorScript.connectionMode == "MQTT_SSL":
            messagebox.showinfo("Information", "The data will be transmitted securely with SSL.")
        else:
            messagebox.showinfo("Information", "The data will be transmitted via HTTP.")
        
        # Iniciar la simulación en un nuevo hilo
        self.simulation_thread = threading.Thread(target=iotSimulatorScript.main)
        self.simulation_running = True
        self.simulation_thread.start()

        # Iniciar el suscriptor en un nuevo hilo si el modo es MQTT
        if iotSimulatorScript.connectionMode in ["MQTT_NO_SSL", "MQTT_SSL"]:
            self.subscriber_thread = threading.Thread(target=self.start_subscriber)
            self.subscriber_thread.start()


    def start_subscriber(self):
        iotSubscriberNoCrypto.main(callback=self.display_message)


    def display_message(self, message):
        self.messages_textbox.insert(tk.END, message + "\n")
        self.messages_textbox.see(tk.END)

    def stop_simulation(self):
        if not self.simulation_running:
            messagebox.showwarning("Warning", "No simulation is running.")
            return

        # Detener la simulación y el suscriptor
        iotSimulatorScript.running = False
        iotSubscriberNoCrypto.running = False

        if self.simulation_thread:
            self.simulation_thread.join()

        if self.subscriber_thread:
            self.subscriber_thread.join()

        self.simulation_running = False

        # Limpiar la caja de texto de mensajes
        self.messages_textbox.delete(1.0, tk.END)

        messagebox.showinfo("Information", "Simulation stopped.")


if __name__ == "__main__":
    root = tk.Tk()
    app = IoTApp(root)
    root.mainloop()
