#!/usr/bin/env python3
import json
import os
import sys


ROOT = "/Users/localuser/msa"


def exists(path: str) -> bool:
    return os.path.exists(path)


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    sys.exit(1)


def check_templates() -> None:
    manifest_path = os.path.join(ROOT, "templates/manifest.json")
    if not exists(manifest_path):
        fail("templates/manifest.json is missing")
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or len(data) < 20:
        fail("Template manifest must contain at least 20 entries with metadata")
    # Spot-check required keys on first entry
    required = {"id", "name", "jurisdiction", "use_cases", "source_url"}
    if not required.issubset(set(data[0].keys())):
        fail("Template manifest entries must include id, name, jurisdiction, use_cases, source_url")
    print(f"[OK] Templates: {len(data)} entries")


def check_schema() -> None:
    json_path = os.path.join(ROOT, "intake_schema/hubspot_properties.json")
    csv_path = os.path.join(ROOT, "intake_schema/schema.csv")
    if not exists(json_path) or not exists(csv_path):
        fail("Intake schema JSON and CSV not found")
    with open(json_path, "r", encoding="utf-8") as f:
        props = json.load(f)
    if not isinstance(props, list) or len(props) < 15:
        fail("Intake schema should have a reasonable number of properties (>=15)")
    print(f"[OK] Intake schema: {len(props)} properties")


def check_mock() -> None:
    mock_json = os.path.join(ROOT, "mock_data/mock_dataset.json")
    if not exists(mock_json):
        fail("mock_data/mock_dataset.json is missing")
    with open(mock_json, "r", encoding="utf-8") as f:
        rows = json.load(f)
    if not isinstance(rows, list) or len(rows) < 50:
        fail("Mock dataset must have at least 50 records")
    print(f"[OK] Mock dataset: {len(rows)} records")


def check_feedback() -> None:
    log_dir = os.path.join(ROOT, "context/orchestration/logs")
    if not exists(log_dir):
        fail("Feedback logs directory missing: context/orchestration/logs")
    print("[OK] Feedback logs directory exists")


def main() -> None:
    check_templates()
    check_schema()
    check_mock()
    check_feedback()
    print("All QA checks passed.")


if __name__ == "__main__":
    main()


