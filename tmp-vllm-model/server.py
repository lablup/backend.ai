"""Simple OpenAI-compatible mock server for vLLM image deployment testing."""
import json
import socket
import time
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self._json_response(200, {"status": "healthy"})
        elif self.path == "/v1/models":
            self._json_response(200, {
                "object": "list",
                "data": [{"id": "test-model", "object": "model", "owned_by": "test"}],
            })
        else:
            self._json_response(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/v1/chat/completions":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length else b"{}"
            request_data = json.loads(body)
            messages = request_data.get("messages", [])
            user_message = ""
            for message in messages:
                if message.get("role") == "user":
                    user_message = message.get("content", "")

            self._json_response(200, {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": "test-model",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"Echo: {user_message}",
                    },
                    "finish_reason": "stop",
                }],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            })
        else:
            self._json_response(404, {"error": "not found"})

    def _json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        # quieter logging
        pass


if __name__ == "__main__":
    ip = socket.gethostbyname(socket.gethostname())
    server = HTTPServer(("", 8000), Handler)
    print(f"Server running on {ip}:8000")
    server.serve_forever()
