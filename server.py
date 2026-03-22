#!/usr/bin/env python3
"""Packing list web app - manage items and push to Todoist."""

import json
import os
import sys
import uuid
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE = os.path.join(SCRIPT_DIR, "packing.template.json")
HTML_FILE = os.path.join(SCRIPT_DIR, "index.html")
CSS_FILE = os.path.join(SCRIPT_DIR, "coefficiencies.css")

SYNC_URL = "https://api.todoist.com/api/v1/sync"


def load_data():
    with open(JSON_FILE) as f:
        return json.load(f)


def send_to_todoist(task_name, selected_tags, api_key):
    data = load_data()
    commands = []

    parent_temp_id = str(uuid.uuid4())
    commands.append({
        "type": "item_add",
        "temp_id": parent_temp_id,
        "uuid": str(uuid.uuid4()),
        "args": {"content": task_name},
    })

    for cat in data["categories"]:
        # Include if "always" or if any tag matches
        if "always" in cat["tags"] or any(t in selected_tags for t in cat["tags"]):
            cat_temp_id = str(uuid.uuid4())
            commands.append({
                "type": "item_add",
                "temp_id": cat_temp_id,
                "uuid": str(uuid.uuid4()),
                "args": {
                    "content": f"**{cat['name']}**",
                    "parent_id": parent_temp_id,
                },
            })
            for item in cat["items"]:
                commands.append({
                    "type": "item_add",
                    "temp_id": str(uuid.uuid4()),
                    "uuid": str(uuid.uuid4()),
                    "args": {
                        "content": item,
                        "parent_id": cat_temp_id,
                    },
                })

    req_data = json.dumps({"commands": commands}).encode("utf-8")
    req = urllib.request.Request(
        SYNC_URL,
        data=req_data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())

    errors = []
    if "sync_status" in result:
        errors = [k for k, v in result["sync_status"].items() if v != "ok"]

    return {"total": len(commands), "errors": len(errors)}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Quieter logging
        pass

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/":
            with open(HTML_FILE, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)

        elif path == "/coefficiencies.css":
            with open(CSS_FILE, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/css")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)

        elif path == "/api/data":
            self._send_json(load_data())

        else:
            self.send_error(404)

    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/api/send":
            body = self._read_body()
            task_name = body.get("task_name", "Packing")
            selected_tags = body.get("tags", [])
            api_key = body.get("api_key", "").strip()
            if not api_key:
                self._send_json({"error": "No API key provided."}, 400)
                return
            try:
                result = send_to_todoist(task_name, selected_tags, api_key)
                self._send_json(result)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)

        else:
            self.send_error(404)


def main():
    port = int(os.environ.get("PORT", sys.argv[1] if len(sys.argv) > 1 else 8420))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Packing list app running at http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
