#!/usr/bin/env python3
"""Fail closed when private records or personal contact data enter the public site."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {
    ".html", ".htm", ".md", ".txt", ".json", ".js", ".css",
    ".xml", ".yml", ".yaml", ".csv", ".ts", ".tsx", ".py",
}
PRIVATE_PATH_PARTS = {
    "snap",
    "ncr_atleos_legal_case",
    "05_legal_and_financial",
}
PRIVATE_FILENAMES = {
    "sponsor_outreach_queue.json",
}
PHONE_RE = re.compile(
    r"(?<!\d)(?:\+?1[ .-]?)?(?:\(\d{3}\)|\d{3})[ .-]\d{3}[ .-]\d{4}(?!\d)"
)
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CASE_ID_RE = re.compile(r"\b(?:case|edg)\s*(?:#|id)?\s*\d{6,12}\b", re.IGNORECASE)
TEL_LINK_RE = re.compile(r"href\s*=\s*['\"]tel:", re.IGNORECASE)
ADDRESS_RE = re.compile(
    r"\b\d{1,6}\s+[A-Z0-9.' -]{3,40}\s"
    r"(?:St|Street|Ave|Avenue|Rd|Road|Dr|Drive|Ln|Lane|Ct|Court|Blvd|Boulevard|Way|Pkwy|Parkway)\b",
    re.IGNORECASE,
)


def path_violations(relative_path: str) -> list[str]:
    path = Path(relative_path)
    parts = {part.lower() for part in path.parts}
    problems = []
    if parts & PRIVATE_PATH_PARTS:
        problems.append("private_path")
    if path.name.lower() in PRIVATE_FILENAMES:
        problems.append("private_outreach_queue")
    if path.suffix.lower() == ".pdf":
        problems.append("unreviewed_pdf")
    return problems


def content_violations(content: str) -> list[str]:
    problems = []
    if PHONE_RE.search(content) or TEL_LINK_RE.search(content):
        problems.append("phone_number_or_tel_link")
    if SSN_RE.search(content):
        problems.append("ssn_pattern")
    if CASE_ID_RE.search(content):
        problems.append("case_or_edg_identifier")
    if ADDRESS_RE.search(content):
        problems.append("street_address")
    return problems


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return [entry.decode("utf-8", "surrogateescape") for entry in result.stdout.split(b"\0") if entry]


def main() -> int:
    try:
        files = tracked_files()
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"[PRIVACY GUARD] Could not enumerate tracked files: {exc}", file=sys.stderr)
        return 2

    violations = []
    for relative in files:
        reasons = path_violations(relative)
        if reasons:
            violations.append((relative, reasons))
            continue

        path = ROOT / relative
        if path.suffix.lower() not in TEXT_SUFFIXES or not path.is_file():
            continue

        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            violations.append((relative, ["unreadable_file"]))
            continue

        reasons = content_violations(content)
        if reasons:
            violations.append((relative, reasons))

    if violations:
        print(f"[PRIVACY GUARD] BLOCKED: {len(violations)} file(s) require review.")
        for relative, reasons in violations:
            print(f" - {relative}: {', '.join(reasons)}")
        return 1

    print(f"[PRIVACY GUARD] PASS: scanned {len(files)} tracked files; no blocked private paths or personal-data patterns found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
