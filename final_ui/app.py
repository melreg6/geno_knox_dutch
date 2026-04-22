# app.py
from flask import Flask, request, jsonify, render_template
from db import load_parts
from knox_proxy import proxy_request
from config import PORT
from urllib.parse import urlsplit


app = Flask(__name__)

parts = load_parts()

@app.route("/")
def index():
    return render_template("index.html", parts=parts)

@app.route("/knox/<path:endpoint>", methods=["GET", "POST"])
def knox(endpoint):
    body = None
    headers = {}

    if request.method == "POST":
        body = request.get_data()
        headers["Content-Type"] = request.content_type or ""

    query = (
        "?" + request.query_string.decode()
        if request.query_string else ""
    )

    # ✅ Correct path (no /knox prefix)
    forward_path = f"/{endpoint}{query}"

    print(f"Proxying {request.method} {forward_path} to Knox...")

    data, status, resp_headers = proxy_request(
        request.method,
        forward_path,
        body,
        headers
    )

    return (data, status, resp_headers.items())

if __name__ == "__main__":
    print(f"Running on http://localhost:{PORT}")
    app.run(port=PORT, debug=True)