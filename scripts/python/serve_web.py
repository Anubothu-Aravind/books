"""
serve_web.py

Starts a simple Python HTTP server pointing to the repository web/ directory,
allowing local interaction with the CrossRefViz visualizer dashboard.

Usage:
    python scripts/python/serve_web.py
"""

import http.server
import socketserver
import os
import sys

PORT = 8000

script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(os.path.dirname(script_dir))
web_dir = os.path.join(base_dir, "web")

if not os.path.exists(web_dir):
    print(f"Error: web/ directory does not exist at {web_dir}")
    sys.exit(1)

# serve from base_dir directly to allow relative paths above web/ to succeed
os.chdir(base_dir)

Handler = http.server.SimpleHTTPRequestHandler

# Allow reusing address
class MyTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

print(f"Starting server for CrossRefViz...")
print(f"Serving files from: {base_dir}")

try:
    with MyTCPServer(("", PORT), Handler) as httpd:
        print(f"\n==================================================")
        print(f"   CrossRefViz dashboard is running successfully!")
        print(f"   Open in your browser: http://localhost:{PORT}/web/crossrefviz/")
        print(f"==================================================")
        print("Press Ctrl+C to stop the server.")
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\nStopping server.")
    sys.exit(0)
except Exception as e:
    print(f"Error starting server: {e}")
    sys.exit(1)
