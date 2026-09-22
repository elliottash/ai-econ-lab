"""Tests over the real section data (src/data/sections.yaml + sections/*.yaml)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

SITE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE_ROOT / "scripts"))

from load_sections import load_sections, manifest_entries, section_files_on_disk  # noqa: E402

EXPECTED_HOMEPAGE_SECTIONS = {
    "Recent Working Papers",
    "Selected Publications — Economics",
    "Selected Publications — Political Science",
    "Selected Publications — AI/ML/NLP",
    "Selected Publications — Law",
}

EXPECTED_TOTAL_AT_MIGRATION = 78


class RealDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sections = load_sections()

    def test_nine_sections_in_manifest_order(self):
        self.assertEqual([t for t, _, _ in self.sections], [
            "Recent Working Papers",
            "Selected Publications — Economics",
            "Selected Publications — AI/ML/NLP",
            "Selected Publications — Political Science",
            "Selected Publications — Law",
            "More Working Papers",
            "Peer-Reviewed Journal Articles",
            "Peer-Reviewed Conference Proceedings",
            "Other Publications (Not Peer-Reviewed)",
        ])

    def test_every_section_non_empty(self):
        for title, fname, papers in self.sections:
            self.assertTrue(papers, f"{fname} is empty")

    def test_total_paper_count_floor(self):
        total = sum(len(papers) for _, _, papers in self.sections)
        self.assertGreaterEqual(total, EXPECTED_TOTAL_AT_MIGRATION)

    def test_homepage_sections_are_the_five_expected(self):
        entries = manifest_entries()
        homepage = {e["title"] for e in entries if e.get("on_homepage")}
        self.assertEqual(homepage, EXPECTED_HOMEPAGE_SECTIONS)

    def test_manifest_lists_every_file_on_disk(self):
        listed = {e["file"] for e in manifest_entries()}
        self.assertEqual(listed, section_files_on_disk())

    def test_every_paper_has_title_and_summary(self):
        # Gate that activates once summaries are drafted (M5). Until the first
        # summary lands, the migration is allowed to run summary-less.
        any_summary = any(p.get("summary") for _, _, papers in self.sections for p in papers)
        for title, fname, papers in self.sections:
            for paper in papers:
                self.assertTrue(str(paper.get("title", "")).strip(),
                                f"{fname}: paper without title")
                if any_summary:
                    self.assertTrue(str(paper.get("summary", "")).strip(),
                                    f"{fname}: {paper.get('title')!r} has no summary")

    def test_urls_are_valid(self):
        def ok(url):
            if not url:
                return True
            if url.startswith("/"):
                return not url.startswith("//")
            return url.startswith(("http://", "https://"))

        for title, fname, papers in self.sections:
            for paper in papers:
                for field in ("pdf", "url"):
                    self.assertTrue(ok(paper.get(field)),
                                    f"{fname}: bad {field} {paper.get(field)!r}")
                for field in ("links", "press"):
                    for link in paper.get(field) or []:
                        self.assertTrue(ok(link.get("url")),
                                        f"{fname}: bad {field} url {link.get('url')!r}")

    def test_titles_unique_across_sections(self):
        seen: dict[str, str] = {}
        for title, fname, papers in self.sections:
            for paper in papers:
                norm = " ".join(str(paper.get("title", "")).split()).casefold()
                if norm in seen:
                    self.fail(f"duplicate title {paper['title']!r} in {seen[norm]} and {fname}")
                seen[norm] = fname


if __name__ == "__main__":
    unittest.main()
