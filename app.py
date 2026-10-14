#!/usr/bin/env python3
"""
IBM z/OS JCL Generator Web Application
Runs 100% locally offline without internet access.
Uses Flask by default, with an automatic built-in Python `http.server` fallback
so it can even run in air-gapped environments with zero third-party packages installed.
"""

import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from jcl_engine import UTILITY_METADATA, generate_full_jcl

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# ---------------------------------------------------------------------------
# Flask App Setup (Primary Mode)
# ---------------------------------------------------------------------------
try:
    from flask import Flask, jsonify, render_template, request

    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False

if HAS_FLASK:
    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, "templates"),
        static_folder=os.path.join(BASE_DIR, "static"),
    )

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/utilities", methods=["GET"])
    def api_utilities():
        return jsonify({"utilities": UTILITY_METADATA})

    @app.route("/api/generate", methods=["POST"])
    def api_generate():
        payload = request.get_json(force=True, silent=True) or {}
        try:
            result = generate_full_jcl(payload)
            return jsonify(result)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

# ---------------------------------------------------------------------------
# Standard-Library HTTP Server Fallback (Zero-Dependency Offline Mode)
# ---------------------------------------------------------------------------
class FallbackJCLHandler(BaseHTTPRequestHandler):
    def _send_json(self, data: dict, status: int = 200):
        raw = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/" or path == "/index.html":
            index_file = os.path.join(BASE_DIR, "templates", "index.html")
            with open(index_file, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        if path == "/api/utilities":
            self._send_json({"utilities": UTILITY_METADATA})
            return

        if path.startswith("/static/"):
            rel_path = path.lstrip("/")
            full_path = os.path.abspath(os.path.join(BASE_DIR, rel_path))
            if full_path.startswith(os.path.join(BASE_DIR, "static")) and os.path.isfile(full_path):
                mime, _ = mimetypes.guess_type(full_path)
                with open(full_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", mime or "application/octet-stream")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        payload = json.loads(body or "{}")

        if parsed.path == "/api/generate":
            try:
                result = generate_full_jcl(payload)
                self._send_json(result)
            except ValueError as exc:
                self._send_json({"error": str(exc)}, status=400)
            return

        self.send_error(404, "Not Found")


def run_server(host: str = "127.0.0.1", port: int = 5000):
    if HAS_FLASK:
        print(f"Starting JCL Generator Web App (Flask) at http://{host}:{port}")
        app.run(host=host, port=port, debug=False)
    else:
        print(f"Flask not found; starting built-in Python HTTP server at http://{host}:{port}")
        server = HTTPServer((host, port), FallbackJCLHandler)
        server.serve_forever()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    host = os.environ.get("HOST", "127.0.0.1")
    run_server(host=host, port=port)
