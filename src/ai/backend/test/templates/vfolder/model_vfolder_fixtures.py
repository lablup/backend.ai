# TODO: If possible, change it to a simpler fixture.
MODEL_SERVER_FIXTURE = """\
from http.server import BaseHTTPRequestHandler, HTTPServer

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()

def run(server_class=HTTPServer, handler_class=HealthCheckHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

if __name__ == '__main__':
    run()
"""

MODEL_DEFINITION_FIXTURE = """\
models:
  - name: "test-server"
    model_path: "/models"
    service:
      start_command:
        - python
        - server.py
      port: 8000
      health_check:
        path: /health
        max_retries: 5
"""
