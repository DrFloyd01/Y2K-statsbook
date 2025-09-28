from flask import Flask, send_from_directory
import os

# This creates a simple web server that is more robust than Python's
# built-in http.server, especially for environments like Codespaces.

app = Flask(__name__, static_folder=os.path.abspath('site'))

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')