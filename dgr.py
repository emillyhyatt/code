import time
import requests
from flask import Flask, jsonify, render_template_string
import threading
from dotenv import load_dotenv
import os
import logging
from flask.logging import default_handler

# Load environment variables from .env file
load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
CODESPACE_NAME = os.getenv('CODESPACE_NAME')
OWNER = os.getenv('OWNER')
REPO = os.getenv('REPO')

headers = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github+json'
}

app = Flask(__name__)

# Disable default Flask request logging
app.logger.removeHandler(default_handler)

script_running = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def get_codespace_status():
    url = f'https://api.github.com/user/codespaces/{CODESPACE_NAME}'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        logging.info(f'Codespace Status Response: {data}')  # Debugging output
        return data.get('state')
    elif response.status_code == 404:
        logging.error('Codespace not found.')
        return None
    else:
        logging.error(f'Error fetching codespace status: {response.status_code} - {response.text}')
        return None

def start_codespace():
    url = f'https://api.github.com/user/codespaces/{CODESPACE_NAME}/start'
    retries = 3
    for attempt in range(retries):
        response = requests.post(url, headers=headers)
        if response.status_code == 202:
            logging.info('Codespace starting...')
            return True
        elif response.status_code == 409:
            logging.info('Codespace is already starting or running.')
            return True
        else:
            logging.error(f'Attempt {attempt + 1}: Error starting codespace: {response.status_code} - {response.text}')
            time.sleep(5)  # Wait 5 seconds before retrying
    return False

@app.route('/alive', methods=['GET'])
def alive():
    return jsonify({"status": "I'm alive"}), 200

@app.route('/')
def home():
    global script_running
    status = "I'm alive" if script_running else "I'm not running"
    html_content = f"""
    <html>
        <head>
            <title>Script Status</title>
        </head>
        <body>
            <h1>{status}</h1>
        </body>
    </html>
    """
    return render_template_string(html_content)

@app.route('/health', methods=['GET'])
def health():
    global script_running
    monitoring_status = "running" if script_running else "stopped"
    return jsonify({"monitoring_thread": monitoring_status}), 200

def monitor_codespace():
    global script_running
    logging.info("Monitoring thread started.")  # Log when the thread starts

    while True:
        logging.info("Checking codespace status...")  # Log every status check
        status = get_codespace_status()
        logging.info(f"Current Codespace Status: {status}")

        if status == 'Available':
            logging.info('Codespace is already running.')
            script_running = True
        elif status in ['Stopped', 'Shutdown']:
            logging.info('Codespace is not running. Starting...')
            if start_codespace():
                script_running = True
            else:
                script_running = False
        elif status is None:
            logging.info('Unable to determine codespace status.')
            script_running = False
        else:
            logging.info(f'Unhandled codespace status: {status}')
            script_running = False

        time.sleep(5)

if __name__ == "__main__":
    threading.Thread(target=monitor_codespace).start()
    app.run(host='0.0.0.0', port=10000, threaded=True)  # Ensure threading is enabled
