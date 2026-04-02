"""Minimal HTTP server for E2E model store testing.

Provides a health check endpoint so that deployment routes
can transition to HEALTHY status during E2E tests.
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/health":
            body = json.dumps({"status": "healthy"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(200)
            self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        pass  # suppress request logs


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8000), Handler)
    print("serve.py listening on :8000")
    server.serve_forever()
