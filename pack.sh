#!/usr/bin/env python3
"""CLI packing list sender - reads packing.json and sends to Todoist."""

import json
import os
import sys
import uuid
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_local = os.path.join(SCRIPT_DIR, "packing.json")
_template = os.path.join(SCRIPT_DIR, "packing.template.json")
JSON_FILE = _local if os.path.exists(_local) else _template

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


def main():
    with open(JSON_FILE) as f:
        data = json.load(f)

    questions = data["questions"]
    all_tags = [q["id"] for q in questions]

    print("What kind of trip is this?\n")
    selected = set()
    for q in questions:
        answer = input(f"  {q['label']} (y/n) ").strip().lower()
        if answer in ("y", "yes"):
            selected.add(q["id"])

    task_name = input("\nTask name [Packing]: ").strip() or "Packing"

    # Filter categories
    matched = [c for c in data["categories"]
               if "always" in c["tags"] or any(t in selected for t in c["tags"])]

    commands = []
    parent_temp_id = str(uuid.uuid4())
    commands.append({
        "type": "item_add",
        "temp_id": parent_temp_id,
        "uuid": str(uuid.uuid4()),
        "args": {"content": task_name},
    })

    item_count = 0
    for cat in matched:
        cat_temp_id = str(uuid.uuid4())
        commands.append({
            "type": "item_add",
            "temp_id": cat_temp_id,
            "uuid": str(uuid.uuid4()),
            "args": {"content": f"**{cat['name']}**", "parent_id": parent_temp_id},
        })
        for item in cat["items"]:
            commands.append({
                "type": "item_add",
                "temp_id": str(uuid.uuid4()),
                "uuid": str(uuid.uuid4()),
                "args": {"content": item, "parent_id": cat_temp_id},
            })
            item_count += 1

    print(f"\nSending {item_count} items to Todoist...")

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

    if "sync_status" in result:
        errors = [k for k, v in result["sync_status"].items() if v != "ok"]
        if errors:
            print(f"Warning: {len(errors)} items had issues.")
        else:
            print(f"Done! Check your Todoist inbox for '{task_name}'.")
    else:
        print("Done! Check your Todoist inbox.")


if __name__ == "__main__":
    main()
