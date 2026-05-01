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
    data, status, _ = proxy_request(
        "GET",
        "/designSpace/enumerate?targetSpaceID=ui_design&numDesigns=100&bfs=false&allDesigns=true"
    )

    designs = data.decode() if data else "[]"

    return render_template("index.html", parts=parts, designs=designs)

from flask import Response

@app.route("/knox/<path:endpoint>", methods=["GET", "POST"])
def knox(endpoint):
    body = None
    headers = {}

    if request.method == "POST":
        body = request.get_data()
        headers["Content-Type"] = request.content_type or ""

    query = "?" + request.query_string.decode() if request.query_string else ""
    forward_path = f"/{endpoint}{query}"

    data, status, resp_headers = proxy_request(
        request.method,
        forward_path,
        body,
        headers
    )

    return Response(
        data,
        status=status,
        content_type=resp_headers.get("Content-Type", "application/json")
    )

if __name__ == "__main__":
    print(f"Running on http://localhost:{PORT}")
    app.run(port=PORT, debug=True)