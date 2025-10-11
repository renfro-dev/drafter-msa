#!/usr/bin/env python3
import json
import os
import re
import time
from typing import Any, Dict, List

import requests
import yaml


ROOT = "/Users/localuser/msa"
TARGETS_YAML = os.path.join(ROOT, "scripts/scrape/targets.yaml")
RAW_DIR = os.path.join(ROOT, "templates/raw")
MANIFEST_PATH = os.path.join(ROOT, "templates/manifest.json")


def ensure_dirs() -> None:
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value


def load_targets() -> List[Dict[str, Any]]:
    with open(TARGETS_YAML, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_manifest() -> List[Dict[str, Any]]:
    if not os.path.exists(MANIFEST_PATH):
        return []
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_manifest(entries: List[Dict[str, Any]]) -> None:
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)


def already_in_manifest(entries: List[Dict[str, Any]], target_id: str) -> bool:
    return any(e.get("id") == target_id for e in entries)


def fetch_and_store(target: Dict[str, Any]) -> Dict[str, Any]:
    url = target["url"]
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    filename = f"{target['id']}-{slugify(target['name'])}.bin"
    path = os.path.join(RAW_DIR, filename)
    with open(path, "wb") as f:
        f.write(response.content)
    return {
        "id": target["id"],
        "name": target["name"],
        "jurisdiction": target.get("jurisdiction"),
        "use_cases": target.get("use_cases", []),
        "source_url": url,
        "local_path": os.path.relpath(path, ROOT),
        "access": "public",
        "fetched_at": int(time.time())
    }


def main() -> None:
    ensure_dirs()
    targets = load_targets()
    manifest = load_manifest()
    updated = False
    for t in targets:
        if already_in_manifest(manifest, t["id"]):
            continue
        try:
            entry = fetch_and_store(t)
            manifest.append(entry)
            updated = True
            print(f"Fetched: {t['name']}")
        except Exception as e:
            print(f"Skip {t['id']}: {e}")
    if updated:
        save_manifest(manifest)
        print(f"Manifest updated: {MANIFEST_PATH}")
    else:
        print("No new entries added to manifest.")


if __name__ == "__main__":
    main()


