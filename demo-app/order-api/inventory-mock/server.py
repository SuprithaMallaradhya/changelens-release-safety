import json
from http.server import BaseHTTPRequestHandler, HTTPServer

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/actuator/health":
            self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
            self.wfile.write(b'{"status":"UP"}')
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != "/inventory/reservations":
            self.send_error(404); return
        length = int(self.headers.get("Content-Length", 0)); body = json.loads(self.rfile.read(length) or b"{}")
        reserved = bool(body.get("sku")) and int(body.get("quantity", 0)) > 0
        payload = json.dumps({"reserved": reserved}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(payload))); self.end_headers(); self.wfile.write(payload)

    def log_message(self, format, *args):
        return

HTTPServer(("0.0.0.0", 8081), Handler).serve_forever()
