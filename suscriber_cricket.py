import sys
import json
import sqlite3
import os
import threading
import signal
from datetime import datetime
import math

from openpyxl import Workbook, load_workbook
import paho.mqtt.client as mqtt

# Configuración
BROKER = "192.168.0.101"
PORT = 1884
TOPIC = "esp32/sensores/crickethub1"
DB_FILE = "datos_sensores.db"
EXCEL_FILE = "mediciones.xlsx"

# Función para limpiar valores
def parse_float(value):
    try:
        val = float(value)
        if math.isnan(val) or math.isinf(val):
            return None
        return val
    except:
        return None

# Base de datos
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

# Excel
if not os.path.exists(EXCEL_FILE):
    wb = Workbook()
    ws = wb.active
    ws.title = "Datos"
    ws.append(["timestamp", "accel_x", "accel_y", "accel_z", "lux", "temp", "humidity", "co2"])
    wb.save(EXCEL_FILE)

# MQTT Callbacks
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
            payload.get("timestamp"),
            parse_float(payload.get("accel_x")),
            parse_float(payload.get("accel_y")),
            parse_float(payload.get("accel_z")),
            parse_float(payload.get("lux")),
            parse_float(payload.get("temp")),
            parse_float(payload.get("humidity")),
            parse_float(payload.get("co2")),
        )

        # Guardar en DB
        cursor.execute("""
        INSERT INTO mediciones (timestamp, accel_x, accel_y, accel_z, lux, temp, humidity, co2)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, fila)
        conn.commit()

        # Guardar en Excel
        wb = load_workbook(EXCEL_FILE)
        ws = wb["Datos"]
        ws.append(fila)
        wb.save(EXCEL_FILE)

        print("📥 Datos almacenados:")
        print(json.dumps(payload, indent=2))

    except Exception as e:
        print(f"⚠️ Error procesando mensaje: {e}")

# MQTT Worker
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
