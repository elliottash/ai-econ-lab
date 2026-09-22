"""Shared loader for the YAML research sections (audit + tests use this).

Reads src/data/sections.yaml (the manifest: file, title, on_homepage) and each
listed file under src/data/sections/. Returns a list of
(manifest_title, file_name, papers) tuples in manifest order. YAML syntax
errors are re-raised with the file name so the user sees which file to fix.
"""
from __future__ import annotations

from pathlib import Path

import yaml

SITE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = SITE_ROOT / "src" / "data"


def load_sections(data_dir: Path = DATA_DIR) -> list[tuple[str, str, list[dict]]]:
    manifest_path = data_dir / "sections.yaml"
    try:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"YAML error in {manifest_path.name}:\n{exc}") from exc
    if not isinstance(manifest, dict) or not isinstance(manifest.get("sections"), list):
        raise ValueError(f"{manifest_path.name} must contain a 'sections' list")

    sections: list[tuple[str, str, list[dict]]] = []
    for entry in manifest["sections"]:
        file_name = entry["file"]
        path = data_dir / "sections" / file_name
        try:
            papers = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ValueError(f"YAML error in sections/{file_name}:\n{exc}") from exc
        if papers is None:
            papers = []
        if not isinstance(papers, list) or not all(isinstance(p, dict) for p in papers):
            raise ValueError(f"sections/{file_name} must contain a YAML list of papers")
        sections.append((entry["title"], file_name, papers))
    return sections


def manifest_entries(data_dir: Path = DATA_DIR) -> list[dict]:
    return yaml.safe_load((data_dir / "sections.yaml").read_text(encoding="utf-8"))["sections"]


def section_files_on_disk(data_dir: Path = DATA_DIR) -> set[str]:
    return {p.name for p in (data_dir / "sections").glob("*.yaml")}
