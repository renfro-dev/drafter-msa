#!/usr/bin/env python3
import argparse
import difflib
import os
import re
from datetime import datetime
from typing import Tuple


LOG_DIR = "/Users/localuser/msa/context/orchestration/logs"


def ensure_log_dir() -> None:
    os.makedirs(LOG_DIR, exist_ok=True)


def log_event(message: str) -> None:
    ensure_log_dir()
    log_path = os.path.join(LOG_DIR, "feedback.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.utcnow().isoformat()}Z] {message}\n")


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_text(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def create_unified_markdown_diff(old_text: str, new_text: str, fromfile: str, tofile: str) -> str:
    diff_lines = list(
        difflib.unified_diff(
            old_text.splitlines(keepends=False),
            new_text.splitlines(keepends=False),
            fromfile=fromfile,
            tofile=tofile,
            lineterm=""
        )
    )
    # Wrap in fenced code block for Markdown rendering
    return "```diff\n" + "\n".join(diff_lines) + "\n```\n"


def apply_annotations(draft_text: str, request_text: str) -> Tuple[str, int]:
    """Apply lightweight annotations:
    - [REPLACE: old => new]
    - [APPEND: ## Heading | content]
    - [REMOVE: text]
    Returns (revised_text, num_changes).
    """
    changes = 0
    text = draft_text

    # REPLACE
    for match in re.finditer(r"\[REPLACE:\s*(.*?)\s*=>\s*(.*?)\s*\]", request_text, flags=re.DOTALL):
        old, new = match.group(1), match.group(2)
        if old in text:
            text = text.replace(old, new)
            changes += 1

    # REMOVE
    for match in re.finditer(r"\[REMOVE:\s*(.*?)\s*\]", request_text, flags=re.DOTALL):
        target = match.group(1)
        if target in text:
            text = text.replace(target, "")
            changes += 1

    # APPEND (append after last line)
    for match in re.finditer(r"\[APPEND:\s*(.*?)\s*\|\s*(.*?)\s*\]", request_text, flags=re.DOTALL):
        heading, content = match.group(1), match.group(2)
        text = text.rstrip() + f"\n\n{heading}\n\n{content}\n"
        changes += 1

    return text, changes


def cmd_diff(args: argparse.Namespace) -> None:
    old_text = read_text(args.old)
    new_text = read_text(args.new)
    diff_md = create_unified_markdown_diff(old_text, new_text, args.old, args.new)
    os.makedirs(args.out, exist_ok=True)
    out_path = os.path.join(args.out, "diff.md")
    write_text(out_path, diff_md)
    log_event(f"diff created old={args.old} new={args.new} out={out_path}")
    print(f"Wrote diff: {out_path}")


def cmd_apply(args: argparse.Namespace) -> None:
    draft_text = read_text(args.draft)
    request_text = read_text(args.request)
    revised_text, changes = apply_annotations(draft_text, request_text)
    os.makedirs(args.out, exist_ok=True)
    revised_path = os.path.join(args.out, "revised.md")
    write_text(revised_path, revised_text)
    # Also emit diff vs. original
    diff_md = create_unified_markdown_diff(draft_text, revised_text, args.draft, revised_path)
    diff_path = os.path.join(args.out, "diff.md")
    write_text(diff_path, diff_md)
    log_event(f"apply request={args.request} draft={args.draft} revised={revised_path} changes={changes}")
    print(f"Applied {changes} changes. Revised: {revised_path}\nDiff: {diff_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="MSA feedback engine: diff and apply annotations")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_diff = subparsers.add_parser("diff", help="Create Markdown diff between two drafts")
    p_diff.add_argument("--old", required=True)
    p_diff.add_argument("--new", required=True)
    p_diff.add_argument("--out", required=True)
    p_diff.set_defaults(func=cmd_diff)

    p_apply = subparsers.add_parser("apply", help="Apply request annotations to a draft and produce diff")
    p_apply.add_argument("--draft", required=True)
    p_apply.add_argument("--request", required=True)
    p_apply.add_argument("--out", required=True)
    p_apply.set_defaults(func=cmd_apply)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()


