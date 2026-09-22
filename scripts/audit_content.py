#!/usr/bin/env python3
"""Audit the YAML research sections for corruption before every build.

Runs over src/data/sections.yaml + sections/*.yaml (via load_sections), so a
broken YAML file or a bad edit stops the deploy instead of the live site.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from load_sections import load_sections, manifest_entries, section_files_on_disk, DATA_DIR  # noqa: E402


TERMINAL_PUNCTUATION = frozenset(".?!)]}\"'’”")
URL_FIELDS = ("pdf", "url")
LINK_FIELDS = ("links", "press")
KNOWN_FIELDS = frozenset({"title", "meta", "url", "pdf", "links", "press", "abstract", "summary"})
SUMMARY_MIN, SUMMARY_MAX = 40, 400


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    title: str
    message: str


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def looks_truncated(value: str) -> bool:
    text = value.rstrip()
    return bool(text) and text[-1] not in TERMINAL_PUNCTUATION


def valid_url(value: str) -> bool:
    if not value:
        return True
    if value.startswith("/"):
        return not value.startswith("//")
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def audit_papers(papers: list[dict], where: str) -> list[Finding]:
    findings: list[Finding] = []

    if not papers:
        findings.append(Finding("warning", "empty-section", where,
                                "section has no papers (delete the entry from sections.yaml if intentional)"))

    for index, paper in enumerate(papers, 1):
        title = str(paper.get("title", "")).strip()
        label = f"{title} [{where}]" if title else f"record #{index} [{where}]"
        abstract = str(paper.get("abstract", "")).strip()
        meta = str(paper.get("meta", "")).strip()
        summary = str(paper.get("summary", "")).strip()

        unknown = set(paper) - KNOWN_FIELDS
        if unknown:
            findings.append(Finding(
                "error", "unknown-field", label,
                f"unknown field(s) {sorted(unknown)} (typo? known: {sorted(KNOWN_FIELDS)})"))

        if not title:
            findings.append(Finding("error", "missing-title", label, "title is empty"))

        if not abstract:
            findings.append(Finding("warning", "missing-abstract", label, "abstract is empty"))
        elif looks_truncated(abstract):
            findings.append(Finding(
                "error", "truncated-abstract", label,
                f"abstract ends abruptly: {abstract[-60:]!r}"))

        if not summary:
            findings.append(Finding("error", "missing-summary", label,
                                    "summary (1-2 plain sentences) is missing"))
        else:
            if looks_truncated(summary):
                findings.append(Finding("error", "truncated-summary", label,
                                        f"summary ends abruptly: {summary[-60:]!r}"))
            if not (SUMMARY_MIN <= len(summary) <= SUMMARY_MAX):
                findings.append(Finding(
                    "warning", "summary-length", label,
                    f"summary is {len(summary)} chars (aim for {SUMMARY_MIN}-{SUMMARY_MAX})"))

        if len(meta) > 300:
            findings.append(Finding(
                "error", "abstract-in-meta", label,
                f"meta is {len(meta)} characters and likely contains abstract text"))

        for field in URL_FIELDS:
            value = str(paper.get(field, "")).strip()
            if not valid_url(value):
                findings.append(Finding(
                    "error", "invalid-url", label,
                    f"{field} is not a valid HTTP(S) or root-relative URL: {value!r}"))
        if paper.get("url") and paper.get("url") == paper.get("pdf"):
            findings.append(Finding("warning", "url-equals-pdf", label,
                                    "url is identical to pdf; url can be omitted"))

        for field in LINK_FIELDS:
            links = paper.get(field, [])
            if links is None:
                continue
            if not isinstance(links, list):
                findings.append(Finding("error", "invalid-links", label, f"{field} must be a list"))
                continue
            for link_index, link in enumerate(links, 1):
                if not isinstance(link, dict) or not valid_url(str(link.get("url", "")).strip()):
                    findings.append(Finding(
                        "error", "invalid-url", label,
                        f"{field}[{link_index}] has an invalid URL"))

        for field in ("title", "meta", "abstract", "summary"):
            value = str(paper.get(field, ""))
            if re.search(r"&#\d+;|&(?:amp|quot|apos|lt|gt);", value):
                findings.append(Finding(
                    "warning", "unresolved-html-entity", label,
                    f"{field} contains an unresolved HTML entity"))

    return findings


def audit_global(sections: list[tuple[str, str, list[dict]]]) -> list[Finding]:
    findings: list[Finding] = []
    titles: dict[str, list[str]] = defaultdict(list)
    abstracts: dict[str, list[str]] = defaultdict(list)

    for section_title, file_name, papers in sections:
        where = file_name
        for paper in papers:
            label_title = str(paper.get("title", "")).strip()
            label = f"{label_title} [{where}]"
            if label_title:
                titles[normalize_text(label_title)].append(label)
            abstract = str(paper.get("abstract", "")).strip()
            if abstract:
                abstracts[normalize_text(abstract)].append(label)

    for labels in titles.values():
        if len(labels) > 1:
            findings.append(Finding(
                "error", "duplicate-title", labels[0],
                f"same normalized title appears in: {', '.join(labels)}"))

    for abstract, labels in abstracts.items():
        if len(labels) > 1 and len(abstract) >= 120:
            findings.append(Finding(
                "error", "duplicate-abstract", labels[0],
                f"same abstract is assigned to: {', '.join(labels)}"))
    return findings


def audit_manifest(sections: list[tuple[str, str, list[dict]]], data_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    entries = manifest_entries(data_dir)
    listed = {e["file"] for e in entries}
    on_disk = section_files_on_disk(data_dir)

    for extra in sorted(on_disk - listed):
        findings.append(Finding(
            "error", "orphan-section-file", extra,
            "file exists in sections/ but is not listed in sections.yaml"))
    for missing in sorted(listed - on_disk):
        findings.append(Finding(
            "error", "missing-section-file", missing,
            "listed in sections.yaml but the file does not exist"))

    titles = [e["title"] for e in entries]
    if len(titles) != len(set(titles)):
        findings.append(Finding("error", "duplicate-section-title", "sections.yaml",
                                "a section title appears twice"))
    if [t for t in titles if not str(t).strip()]:
        findings.append(Finding("error", "empty-section-title", "sections.yaml",
                                "a section has an empty title"))
    return findings


def print_findings(findings: Iterable[Finding]) -> None:
    grouped: dict[str, list[Finding]] = defaultdict(list)
    for finding in findings:
        grouped[finding.severity].append(finding)

    for severity in ("error", "warning"):
        items = grouped.get(severity, [])
        if not items:
            continue
        print(f"\n{severity.upper()}S ({len(items)})")
        for item in items:
            print(f"  [{item.code}] {item.title}: {item.message}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--allow-missing-summaries", action="store_true",
                        help="downgrade missing summaries to warnings (pre-summary builds only)")
    parser.add_argument("--warnings-as-errors", action="store_true",
                        help="return a failure status when warnings are present")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        sections = load_sections(args.data_dir)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    findings: list[Finding] = []
    for section_title, file_name, papers in sections:
        findings.extend(audit_papers(papers, file_name))
    findings.extend(audit_global(sections))
    findings.extend(audit_manifest(sections, args.data_dir))

    if args.allow_missing_summaries:
        findings = [replace(f, severity="warning") if f.code == "missing-summary" else f
                    for f in findings]

    findings.sort(key=lambda item: (item.severity != "error", item.code, item.title))
    errors = sum(item.severity == "error" for item in findings)
    warnings = sum(item.severity == "warning" for item in findings)
    total = sum(len(papers) for _, _, papers in sections)
    print(f"Audited {total} papers across {len(sections)} sections from {args.data_dir}")
    print_findings(findings)
    counts = Counter(item.code for item in findings)
    if counts:
        print("\nCounts by check:")
        for code, count in sorted(counts.items()):
            print(f"  {code}: {count}")
    print(f"\nSummary: {errors} error(s), {warnings} warning(s)")
    return int(bool(errors or (args.warnings_as_errors and warnings)))


if __name__ == "__main__":
    raise SystemExit(main())
