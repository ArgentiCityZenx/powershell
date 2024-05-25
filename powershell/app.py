from flask import Flask, render_template, request, jsonify
from threading import Thread
import os
import subprocess
import queue

app = Flask(__name__)

# Queue for passing command output from subprocess to web interface
output_queue = queue.Queue()
process = None
running = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run_command', methods=['POST'])
def run_command():
    global process, running
    command = request.json['command']
    files = request.files.getlist('files')
    
    # Save files to a temporary directory
    uploaded_files = []
    for file in files:
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        uploaded_files.append(file_path)

    if not running:
        running = True
        process = Thread(target=run_powershell_command, args=(command, uploaded_files))
        process.start()
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'error', 'message': 'Another command is already running'})

def run_powershell_command(command, files):
    try:
        # Build command to pass files as arguments
        files_args = ' '.join(files)
        full_command = f"{command} {files_args}"

        result = subprocess.run(["powershell", "-Command", full_command], capture_output=True, text=True)
        output_queue.put((result.stdout, result.stderr))
    except Exception as e:
        output_queue.put(("", str(e)))
    global running
    running = False

@app.route('/get_output')
def get_output():
    try:
        stdout, stderr = output_queue.get_nowait()
        return jsonify({'stdout': stdout, 'stderr': stderr})
    except queue.Empty:
        return jsonify({'stdout': '', 'stderr': ''})

if __name__ == '__main__':
    app.config['UPLOAD_FOLDER'] = 'uploads'
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    app.run(debug=True)
