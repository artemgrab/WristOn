from flask import Flask, render_template, Response, url_for
from datetime import datetime
import threading
import queue
import json
import os

app = Flask(__name__, static_folder='static')
result_queue = queue.Queue()
event_log = []
MAX_LOG_ENTRIES = 50  # Максимальна кількість записів у лозі

# Створюємо директорію для статичних файлів, якщо вона не існує
if not os.path.exists('static'):
    os.makedirs('static')

def update_results(results):
    # Перевіряємо результати на наявність подій з високою впевненістю
    for label, score in results.items():
        if score > 0.6 and label.lower() != 'noise':  # Впевненість > 60% і не шум
            event = {
                'label': label,
                'confidence': score,
                'timestamp': datetime.now().strftime("%H:%M:%S")
            }
            event_log.append(event)
            # Обмежуємо розмір логу
            if len(event_log) > MAX_LOG_ENTRIES:
                event_log.pop(0)
    
    result_queue.put({
        'results': results,
        'event_log': event_log,
        'timestamp': datetime.now().strftime("%H:%M:%S")
    })

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/stream')
def stream():
    def event_stream():
        while True:
            try:
                data = result_queue.get(timeout=30)
                yield f"data: {json.dumps(data)}\n\n"
            except queue.Empty:
                yield "data: {}\n\n"

    return Response(event_stream(), mimetype='text/event-stream')

def run_server():
    app.run(host='0.0.0.0', port=5000, debug=False)
    
if __name__ == '__main__':
    run_server()

