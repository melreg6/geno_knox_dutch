import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):

    html_content = ""
    knox_url     = "http://localhost:8080"

    def log_message(self, fmt, *args):
        status = args[1] if len(args) > 1 else ""
        print(f"  {self.path}  →  {status}")

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            self._serve_html()
        elif self.path.startswith("/knox"):
            self._proxy("GET", self.path[5:])
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path.startswith("/knox"):
            length = int(self.headers.get("Content-Length", 0))
            body   = self.rfile.read(length)
            ct     = self.headers.get("Content-Type", "")
            self._proxy("POST", self.path[5:], body=body, content_type=ct)
        else:
            self.send_response(404)
            self.end_headers()

    def _serve_html(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(self.html_content.encode())

    def _proxy(self, method, knox_path, body=None, content_type=""):
        url     = self.knox_url + knox_path
        headers = {}
        if content_type:
            headers["Content-Type"] = content_type
        try:
            req = urllib.request.Request(url, data=body, headers=headers, method=method)
            with urllib.request.urlopen(req) as resp:
                data = resp.read()
                self.send_response(resp.status)
                self.send_header("Content-Type", resp.headers.get("Content-Type", "application/json"))
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            data = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(f"Could not reach Knox: {e}".encode())


def start(html_content, knox_url, port):
    Handler.html_content = html_content
    Handler.knox_url     = knox_url
    HTTPServer.allow_reuse_address = True
    server = HTTPServer(("localhost", port), Handler)
    print(f"  Serving on http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.server_close()