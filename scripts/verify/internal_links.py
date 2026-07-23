#!/usr/bin/env python3
from __future__ import annotations

import html
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

from _common import ROOT, relative, source_files


INLINE_LINK = re.compile(r"!?\[[^\]]*\]\(([^)\n]+)\)")
REFERENCE_LINK = re.compile(r"^\s*\[[^\]]+\]:\s*(?:<([^>]+)>|(\S+))")
HTML_LINK = re.compile(r"(?:href|src)=[\"']([^\"']+)[\"']", re.IGNORECASE)
HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$")
EXPLICIT_ID = re.compile(r"\b(?:id|name)=[\"']([^\"']+)[\"']", re.IGNORECASE)


def _target(raw: str) -> str:
    value = raw.strip()
    if value.startswith("<") and ">" in value:
        return value[1 : value.index(">")]
    return value.split(maxsplit=1)[0].replace("\\ ", " ") if value else ""


def _slug(heading: str) -> str:
    value = re.sub(r"`([^`]*)`", r"\1", heading)
    value = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"<[^>]+>", "", value)
    value = html.unescape(value).strip().lower().replace("_", "")
    value = re.sub(r"[^\w\-\s]", "", value, flags=re.UNICODE)
    return re.sub(r"\s+", "-", value)


def _anchors(path: Path) -> set[str]:
    anchors: set[str] = set()
    duplicates: dict[str, int] = {}
    in_fence = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        anchors.update(EXPLICIT_ID.findall(line))
        match = HEADING.match(line)
        if not match:
            continue
        base = _slug(match.group(1))
        count = duplicates.get(base, 0)
        duplicates[base] = count + 1
        anchors.add(base if count == 0 else f"{base}-{count}")
    return anchors


def main() -> int:
    errors: list[str] = []
    checked = 0
    anchor_cache: dict[Path, set[str]] = {}
    markdown_files = [path for path in source_files() if path.suffix.lower() == ".md"]

    for document in markdown_files:
        in_fence = False
        for number, line in enumerate(document.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith(("```", "~~~")):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            raw_targets = INLINE_LINK.findall(line)
            reference = REFERENCE_LINK.match(line)
            if reference:
                raw_targets.append(reference.group(1) or reference.group(2))
            raw_targets.extend(HTML_LINK.findall(line))

            for raw in raw_targets:
                target = _target(raw)
                if not target or target.startswith(("#", "//", "${", "{{")):
                    if target.startswith("#"):
                        target = f"{document.name}{target}"
                    else:
                        continue
                parsed = urlsplit(target)
                if parsed.scheme or parsed.netloc:
                    continue

                path_text = unquote(parsed.path)
                candidate = document if path_text in {"", document.name} else (
                    ROOT / path_text.lstrip("/") if path_text.startswith("/") else document.parent / path_text
                )
                resolved = candidate.resolve()
                checked += 1
                if resolved != ROOT and ROOT not in resolved.parents:
                    errors.append(f"{relative(document)}:{number}: link escapes the repository: {target}")
                    continue
                if not resolved.exists():
                    errors.append(f"{relative(document)}:{number}: missing link target: {target}")
                    continue
                if parsed.fragment and resolved.is_file() and resolved.suffix.lower() == ".md":
                    anchors = anchor_cache.setdefault(resolved, _anchors(resolved))
                    fragment = unquote(parsed.fragment)
                    if fragment not in anchors:
                        errors.append(f"{relative(document)}:{number}: missing link anchor: {target}")

    if errors:
        print(f"internal-links: FAIL ({len(errors)} error(s))", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"internal-links: OK ({checked} local links across {len(markdown_files)} Markdown files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
