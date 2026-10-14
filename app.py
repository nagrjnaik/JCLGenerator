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
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

from jcl_engine import TEMPLATE_DIR, UTILITY_METADATA, generate_full_jcl

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "generated_jcl")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def list_template_files():
    """Return all `.jcl.tpl` files and their raw contents for inspection/customization."""
    templates = {}
    if os.path.exists(TEMPLATE_DIR):
        for fname in sorted(os.listdir(TEMPLATE_DIR)):
            if fname.endswith(".tpl"):
                fpath = os.path.join(TEMPLATE_DIR, fname)
                with open(fpath, "r", encoding="utf-8") as f:
                    templates[fname] = f.read()
    return templates


def save_generated_jcl_file(file_name: str, jcl_content: str) -> str:
    """Save generated JCL into `generated_jcl/` directory and return its path."""
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", os.path.basename(file_name or "job.jcl"))
    if not safe_name.lower().endswith((".jcl", ".cntl", ".txt")):
        safe_name += ".jcl"
    out_path = os.path.join(OUTPUT_DIR, safe_name)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(jcl_content)
    return out_path


def update_template_file(template_name: str, content: str) -> str:
    """Update a template file inside `jcl_templates/`."""
    safe_name = os.path.basename(template_name)
    if not safe_name.endswith(".jcl.tpl"):
        raise ValueError("Template file must end with .jcl.tpl")
    target = os.path.join(TEMPLATE_DIR, safe_name)
    with open(target, "w", encoding="utf-8") as f:
        f.write(content)
    return target


# ---------------------------------------------------------------------------
# Flask App Setup (Primary Mode)
# ---------------------------------------------------------------------------
try:
    from flask import Flask, Response, jsonify, render_template, request, send_from_directory

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
        return jsonify({"utilities": UTILITY_METADATA, "templates": list_template_files()})

    @app.route("/api/generate", methods=["POST"])
    def api_generate():
        payload = request.get_json(force=True, silent=True) or {}
        result = generate_full_jcl(payload)
        return jsonify(result)

    @app.route("/api/save", methods=["POST"])
    def api_save():
        payload = request.get_json(force=True, silent=True) or {}
        result = generate_full_jcl(payload)
        saved_path = save_generated_jcl_file(result["file_name"], result["jcl"])
        result["saved_path"] = saved_path
        return jsonify(result)

    @app.route("/api/templates", methods=["GET", "POST"])
    def api_templates():
        if request.method == "GET":
            return jsonify({"templates": list_template_files()})
        data = request.get_json(force=True, silent=True) or {}
        tpl_name = data.get("template_name", "")
        tpl_content = data.get("content", "")
        try:
            updated_path = update_template_file(tpl_name, tpl_content)
            return jsonify({"status": "ok", "updated": updated_path, "templates": list_template_files()})
        except Exception as exc:
            return jsonify({"status": "error", "message": str(exc)}), 400


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
            self._send_json({"utilities": UTILITY_METADATA, "templates": list_template_files()})
            return

        if path == "/api/templates":
            self._send_json({"templates": list_template_files()})
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
            result = generate_full_jcl(payload)
            self._send_json(result)
            return

        if parsed.path == "/api/save":
            result = generate_full_jcl(payload)
            saved_path = save_generated_jcl_file(result["file_name"], result["jcl"])
            result["saved_path"] = saved_path
            self._send_json(result)
            return

        if parsed.path == "/api/templates":
            try:
                updated_path = update_template_file(payload.get("template_name", ""), payload.get("content", ""))
                self._send_json({"status": "ok", "updated": updated_path, "templates": list_template_files()})
            except Exception as exc:
                self._send_json({"status": "error", "message": str(exc)}, status=400)
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
