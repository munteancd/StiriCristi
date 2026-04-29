#!/usr/bin/env python3
"""Simple HTTP server for serving the PWA locally."""
import http.server
import socketserver
import os
import webbrowser
import socket
from pathlib import Path

PORT = 8000
DIRECTORY = "pwa"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        # Enable CORS and service worker support
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Service-Worker-Allowed', '/')
        super().end_headers()

def get_local_ip():
    """Get the local IP address for network access."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "localhost"

if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    local_ip = get_local_ip()
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Server running at:")
        print(f"  Local:   http://localhost:{PORT}")
        print(f"  Network: http://{local_ip}:{PORT}")
        print(f"Serving directory: {DIRECTORY}/")
        print("Press Ctrl+C to stop")
        print()
        print(f"To access from phone on same WiFi, use: http://{local_ip}:{PORT}")
        
        # Open browser automatically
        webbrowser.open(f"http://localhost:{PORT}")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped")
