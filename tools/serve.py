from flask import Flask, send_from_directory
import os

# This creates a simple web server that is more robust than Python's
# built-in http.server, especially for environments like Codespaces.

app = Flask(__name__, static_folder=os.path.abspath('site'))

@app.route('/<path:path>')
def serve_static(path):
    """
    Serves a static file from the static folder.

    Args:
        path (str): The path to the file.

    Returns:
        A response object containing the file.
    """
    return send_from_directory(app.static_folder, path)

@app.route('/')
def serve_index():
    """
    Serves the index.html file.

    Returns:
        A response object containing the index.html file.
    """
    return send_from_directory(app.static_folder, 'index.html')