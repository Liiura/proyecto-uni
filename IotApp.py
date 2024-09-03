import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import threading
import iotSimulatorScript
import iotSubscriberNoCrypto

class IoTApp:
    def __init__(self, root):
        self.root = root
        self.root.title("IoT Simulator Control Panel")
        self.root.geometry("400x300")
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

    def start_simulation(self):
        if self.simulation_running:
            messagebox.showwarning("Warning", "Simulation is already running.")
            return
        
        iotSimulatorScript.connectionMode = self.connection_mode.get()
        iotSubscriberNoCrypto.connectionMode = self.connection_mode.get()

        # Display a message based on the connection mode
        if iotSimulatorScript.connectionMode == "MQTT_NO_SSL":
            messagebox.showinfo("Information", "The data will be transmitted in plain text.")
        elif iotSimulatorScript.connectionMode == "MQTT_SSL":
            messagebox.showinfo("Information", "The data will be transmitted securely with SSL.")
        else:
            messagebox.showinfo("Information", "The data will be transmitted via HTTP.")
        
        # Start the simulation in a new thread to prevent blocking the GUI
        self.simulation_thread = threading.Thread(target=iotSimulatorScript.main)
        self.simulation_running = True
        self.simulation_thread.start()

        # Start the subscriber in a new thread if MQTT mode is selected
        if iotSimulatorScript.connectionMode in ["MQTT_NO_SSL", "MQTT_SSL"]:
            self.subscriber_thread = threading.Thread(target=iotSubscriberNoCrypto.main)
            self.subscriber_thread.start()

    def stop_simulation(self):
        if not self.simulation_running:
            messagebox.showwarning("Warning", "No simulation is running.")
            return
        
        # Stop the simulation and subscriber
        iotSimulatorScript.running = False
        iotSubscriberNoCrypto.running = False
        
        if self.simulation_thread:
            self.simulation_thread.join()
        
        if self.subscriber_thread:
            self.subscriber_thread.join()

        self.simulation_running = False
        messagebox.showinfo("Information", "Simulation stopped.")

if __name__ == "__main__":
    root = tk.Tk()
    app = IoTApp(root)
    root.mainloop()
