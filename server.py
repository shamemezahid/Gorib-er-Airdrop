import http.server
import socketserver
import os
import cgi
import threading
import sys
import time
import socket
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FOLDER_NAME = 'shared files'
UPLOAD_DIR = os.path.join(SCRIPT_DIR, FOLDER_NAME)

# makes the shared files directory accessible if it doesn't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)

INITIAL_PORT = 8000

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = f"""
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>File Server</title>
                    <link rel="stylesheet" type="text/css" href="/src/design.css">
                </head>
                <body>
                    <h2 class="section-title">Gorib er Airdrop</h2>
                    <div class="section-container">
                        <h4 class="section-title">Upload File</h4>
                        <form action="/upload" method="post" enctype="multipart/form-data" id="upload-form">
                            <input type="file" name="file" class="file-upload"/>
                            <input type="submit" value="Upload" class="input-button"/>
                        </form>
                    </div>
                    <div class="section-container">
                    <h4 class="section-title">Shared Files:</h4>
                    <div>
            """
            files = os.listdir(UPLOAD_DIR)
            for file in files:
                file_url = f"/{FOLDER_NAME}/{file}"
                html += f'<a href="{file_url}">{file}</a>'
            
            html += f"""
                    </div>
                    </div>
                </body>
                </html>
            """
            self.wfile.write(html.encode('utf-8'))
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/upload':
            form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': self.headers['Content-Type']})
            if 'file' in form:
                file_item = form['file']
                if file_item.filename:
                    file_path = os.path.join(UPLOAD_DIR, os.path.basename(file_item.filename))
                    with open(file_path, 'wb') as file_out:
                        file_out.write(file_item.file.read())
                    # Redirect back to the root page
                    self.send_response(303)
                    self.send_header('Location', '/')
                    self.end_headers()
                else:
                    # Redirect back to the root page
                    self.send_response(303)
                    self.send_header('Location', '/')
                    self.end_headers()
            else:
                self.send_response(400)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'No file field in form.')
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found.')

def find_available_port(starting_port):
    port = starting_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = sock.connect_ex(('localhost', port))
            if result != 0:
                return port
            port += 1

def kill_process_using_port(port):
    try:
        result = subprocess.run(['lsof', '-t', f'-i:{port}'], capture_output=True, text=True)
        if result.stdout:
            pid = result.stdout.strip()
            subprocess.run(['kill', '-9', pid])
            print(f"Process using port {port} has been terminated.")
    except Exception as e:
        print(f"Could not terminate process using port {port}: {e}")

def get_local_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        # This doesn't have to be reachable; it's just for obtaining the local IP
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]

def start_server():
    global PORT, httpd
    PORT = find_available_port(INITIAL_PORT)
    
    handler_object = MyHttpRequestHandler
    
    # Attempt to bind to the chosen port and handle the case where the port is unavailable
    while True:
        try:
            with socketserver.TCPServer(("", PORT), handler_object) as httpd:
                print(f"Serving at port {PORT}")
                print("Server is running. Press Ctrl+C to stop the server.")
                local_ip = get_local_ip()
                print(f"Open your browser and go to: http://{local_ip}:{PORT}")
                # wont work if no internet
                print(f"Open URL as a QR: https://api.qrserver.com/v1/create-qr-code/?size=1000x1000&data={local_ip}:{PORT}")
                httpd.serve_forever()
                break  # Exit loop if server starts successfully
        except OSError as e:
            if "Address already in use" in str(e):
                print(f"Port {PORT} is already in use. Trying the next port...")
                PORT = find_available_port(PORT + 1)
            else:
                raise e
        except KeyboardInterrupt:
            break
    print("Server stopped.")
    httpd.server_close()
    print("Server closed.")

start_server()