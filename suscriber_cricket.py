import sys
import json
import sqlite3
import os
import threading
import signal
from datetime import datetime

from openpyxl import Workbook, load_workbook

import paho.mqtt.client as mqtt

# Config
BROKER = "192.168.0.101"
PORT = 1884
TOPIC = "esp32/sensores/crickethub1"
DB_FILE = "datos_sensores.db"
EXCEL_FILE = "mediciones.xlsx"

# DB setup
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS mediciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    accel_x REAL,
    accel_y REAL,
    accel_z REAL,
    lux REAL,
    temp REAL,
    humidity REAL,
    co2 REAL
)
""")
conn.commit()

# Excel setup
if not os.path.exists(EXCEL_FILE):
    wb = Workbook()
    ws = wb.active
    ws.title = "Datos"
    ws.append(["timestamp", "accel_x", "accel_y", "accel_z", "lux", "temp", "humidity", "co2"])
    wb.save(EXCEL_FILE)

# MQTT callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Conectado al broker MQTT")
        client.subscribe(TOPIC)
    else:
        print(f"❌ Error de conexión MQTT: {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        fila = (
            payload["timestamp"],
            float(payload.get("accel_x", 0)),
            float(payload.get("accel_y", 0)),
            float(payload.get("accel_z", 0)),
            float(payload.get("lux", 0)),
            float(payload.get("temp", 0)),
            float(payload.get("humidity", 0)),
            float(payload.get("co2", 0)),
        )

        # Guardar en DB
        cursor.execute("INSERT INTO mediciones (timestamp, accel_x, accel_y, accel_z, lux, temp, humidity, co2) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", fila)
        conn.commit()

        # Guardar en Excel
        wb = load_workbook(EXCEL_FILE)
        ws = wb["Datos"]
        ws.append(fila)
        wb.save(EXCEL_FILE)

        print("📥 Datos recibidos y almacenados:")
        print(json.dumps(payload, indent=2))

    except Exception as e:
        print(f"⚠️ Error procesando mensaje: {e}")

# MQTT thread
def mqtt_thread_func():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)
    client.loop_forever()

# Main
if __name__ == "__main__":
    try:
        mqtt_thread = threading.Thread(target=mqtt_thread_func)
        mqtt_thread.start()
        mqtt_thread.join()
    except KeyboardInterrupt:
        print("\n🛑 Finalizando programa...")
        conn.close()
        sys.exit(0)
