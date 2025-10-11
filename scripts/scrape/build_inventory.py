#!/usr/bin/env python3
import json
import os
from typing import Any, Dict, List, Set

import yaml


ROOT = "/Users/localuser/msa"
MANIFEST_PATH = os.path.join(ROOT, "templates/manifest.json")
TARGETS_YAML = os.path.join(ROOT, "scripts/scrape/targets.yaml")
OUT_MD = os.path.join(ROOT, "templates/CA_FL_TX_inventory.md")


FOCUS_STATES = {"CA", "FL", "TX"}


def read_manifest() -> List[Dict[str, Any]]:
    if not os.path.exists(MANIFEST_PATH):
        return []
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def read_targets() -> List[Dict[str, Any]]:
    with open(TARGETS_YAML, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def url_kind(url: str) -> str:
    lower = url.lower()
    if lower.endswith(".pdf"): return "pdf"
    if lower.endswith((".doc", ".docx")): return "doc"
    return "html"


def build() -> str:
    manifest = read_manifest()
    targets = read_targets()

    fetched_by_state: Dict[str, List[Dict[str, Any]]] = {s: [] for s in FOCUS_STATES}
    targets_by_state: Dict[str, List[Dict[str, Any]]] = {s: [] for s in FOCUS_STATES}
    fetched_ids: Set[str] = set()

    for entry in manifest:
        j = entry.get("jurisdiction")
        if j in FOCUS_STATES:
            fetched_by_state[j].append(entry)
            fetched_ids.add(entry.get("id", ""))

    for t in targets:
        j = t.get("jurisdiction")
        if j in FOCUS_STATES:
            targets_by_state[j].append(t)

    lines: List[str] = []
    lines.append("## CA/FL/TX MSA Resource Inventory")
    lines.append("")
    lines.append("This file outlines accessible public resources already fetched and targetable sources for California, Florida, and Texas.")
    lines.append("")

    for state in ["CA", "FL", "TX"]:
        lines.append(f"### {state}")
        lines.append("")
        fetched = fetched_by_state[state]
        targets_s = targets_by_state[state]
        lines.append(f"- Fetched: {len(fetched)}")
        for e in fetched:
            name = e.get("name")
            src = e.get("source_url")
            path = e.get("local_path")
            use_cases = ", ".join(e.get("use_cases", []))
            lines.append(f"  - {name} — use_cases: [{use_cases}] — source: `{src}` — saved: `{path}`")
        lines.append(f"- Targets: {len(targets_s)}")
        for t in targets_s:
            tid = t.get("id")
            fetched_flag = "yes" if tid in fetched_ids else "no"
            kind = url_kind(t.get("url", ""))
            name = t.get("name")
            use_cases = ", ".join(t.get("use_cases", []))
            url = t.get("url")
            lines.append(f"  - {name} — kind: {kind} — fetched: {fetched_flag} — use_cases: [{use_cases}] — url: `{url}`")
        lines.append("")

    lines.append("### Notes")
    lines.append("- All items are public/open-access sources. PDFs provide most reliable clause language; HTML pages often provide instructions and links to forms.")
    lines.append("- For California, Judicial Council forms and Self-Help content are key; for Florida, statewide forms (e.g., 902 series) are authoritative; for Texas, TexasLawHelp and state courts provide agreed decree exemplars.")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    content = build()
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()


