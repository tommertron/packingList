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
_local = os.path.join(SCRIPT_DIR, "packing.json")
_template = os.path.join(SCRIPT_DIR, "packing.template.json")
JSON_FILE = _local if os.path.exists(_local) else _template
HTML_FILE = os.path.join(SCRIPT_DIR, "index.html")

# Load .env
env_path = os.path.join(SCRIPT_DIR, ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

API_KEY = os.environ.get("TODOIST_API_KEY", "")
SYNC_URL = "https://api.todoist.com/api/v1/sync"


def load_data():
    with open(JSON_FILE) as f:
        return json.load(f)


def save_data(data):
    with open(JSON_FILE, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def send_to_todoist(task_name, selected_tags):
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
            "Authorization": f"Bearer {API_KEY}",
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

        elif path == "/api/data":
            self._send_json(load_data())

        elif path == "/api/key":
            self._send_json({"set": bool(API_KEY), "key": API_KEY})

        else:
            self.send_error(404)

    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/api/data":
            data = self._read_body()
            save_data(data)
            self._send_json({"ok": True})

        elif path == "/api/key":
            body = self._read_body()
            key = body.get("key", "").strip()
            env_path = os.path.join(SCRIPT_DIR, ".env")
            lines = []
            if os.path.exists(env_path):
                with open(env_path) as f:
                    lines = [l for l in f.readlines() if not l.startswith("TODOIST_API_KEY=")]
            lines.append(f"TODOIST_API_KEY={key}\n")
            with open(env_path, "w") as f:
                f.writelines(lines)
            global API_KEY
            API_KEY = key
            os.environ["TODOIST_API_KEY"] = key
            self._send_json({"ok": True})

        elif path == "/api/send":
            body = self._read_body()
            task_name = body.get("task_name", "Packing")
            selected_tags = body.get("tags", [])
            try:
                result = send_to_todoist(task_name, selected_tags)
                self._send_json(result)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)

        else:
            self.send_error(404)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8420
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Packing list app running at http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
