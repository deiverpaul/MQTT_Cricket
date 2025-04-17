from flask import Flask, jsonify
from datetime import datetime
import pytz

app = Flask(__name__)

@app.route('/api/time')
def get_time():
    tz = pytz.timezone('America/Guayaquil')
    now = datetime.now(tz)
    return jsonify({
        "dateTime": now.strftime("%Y-%m-%dT%H:%M:%S")
    })

if __name__ == '__main__':
    print("🕒 Iniciando API local de hora en http://0.0.0.0:5000/api/time")
    app.run(host='0.0.0.0', port=5000)
