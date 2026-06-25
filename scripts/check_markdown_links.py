#!/usr/bin/env python3

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
LINK_RE = re.compile(r"!?\[[^\]]*]\(([^)\s]+(?:\s+\"[^\"]*\")?)\)")
EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "tel:", "data:")
LOCAL_ABSOLUTE_RE = re.compile(r"^(/[U]sers/|/home/[^/]+/|[A-Za-z]:\\Users\\)")


def strip_fenced_code(text: str) -> str:
    return re.sub(r"```[\s\S]*?```", "", text)


def iter_markdown_files() -> list[Path]:
    return sorted(ROOT.rglob("*.md"))


def normalize_target(raw_target: str) -> str:
    target = raw_target.strip()
    target = re.sub(r'\s+"[^"]*"$', "", target)
    return target.strip("<>")


def main() -> int:
    errors: list[str] = []
    checked = 0
    external = 0

    for path in iter_markdown_files():
        rel = path.relative_to(ROOT).as_posix()
        text = strip_fenced_code(path.read_text(encoding="utf-8"))

        for match in LINK_RE.finditer(text):
            target = normalize_target(match.group(1))
            if not target or target.startswith("#"):
                continue
            if target.startswith(EXTERNAL_PREFIXES):
                external += 1
                continue
            if LOCAL_ABSOLUTE_RE.search(target) or target.startswith("/"):
                errors.append(f"{rel}: absolute local or root link -> {target}")
                continue

            target_path = target.split("#", 1)[0].split("?", 1)[0]
            if not target_path:
                continue

            checked += 1
            resolved = (path.parent / unquote(target_path)).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                errors.append(f"{rel}: link escapes repository -> {target}")
                continue

            if not resolved.exists():
                errors.append(f"{rel}: missing link target -> {target}")

    if errors:
        print("Markdown link check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Markdown link check passed: {checked} internal links, {external} external links")
    return 0


if __name__ == "__main__":
    sys.exit(main())
