"""Tests for the YAML content audit (scripts/audit_content.py)."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

SITE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SITE_ROOT / "scripts"))
from load_sections import load_sections  # noqa: E402
import audit_content  # noqa: E402

GOOD_PAPER = {
    "title": "A Good Paper",
    "meta": "(with A. Coauthor), Journal (2025)",
    "url": "https://example.com/paper",
    "abstract": ("A complete abstract that ends with a period. It is long enough that "
                 "appearing verbatim on two papers signals real duplication, not a "
                 "coincidental match of a short generic sentence."),
    "summary": "One or two plain sentences describing the paper.",
}


class AuditFixture(unittest.TestCase):
    """Writes a scratch data dir and runs the full audit against it."""

    def audit(self, sections: dict[str, list[dict]]) -> list:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "sections").mkdir()
        entries = []
        for i, (title, papers) in enumerate(sections.items()):
            name = f"section-{i}.yaml"
            (root / "sections" / name).write_text(
                yaml.safe_dump(papers, sort_keys=False, allow_unicode=True),
                encoding="utf-8")
            entries.append({"file": name, "title": title, "on_homepage": i == 0})
        (root / "sections.yaml").write_text(
            yaml.safe_dump({"sections": entries}, sort_keys=False, allow_unicode=True),
            encoding="utf-8")

        loaded = load_sections(root)
        findings = []
        for title, fname, papers in loaded:
            findings.extend(audit_content.audit_papers(papers, fname))
        findings.extend(audit_content.audit_global(loaded))
        findings.extend(audit_content.audit_manifest(loaded, root))
        return findings

    @staticmethod
    def codes(findings) -> set:
        return {f.code for f in findings}


class AuditPaperChecks(AuditFixture):
    def test_clean_paper_produces_no_findings(self):
        self.assertEqual(self.codes(self.audit({"S": [dict(GOOD_PAPER)]})), set())

    def test_missing_summary_is_an_error(self):
        paper = dict(GOOD_PAPER)
        del paper["summary"]
        findings = self.audit({"S": [paper]})
        self.assertIn("missing-summary", self.codes(findings))

    def test_truncated_abstract_is_an_error(self):
        paper = dict(GOOD_PAPER, abstract="This abstract stops mid sentence")
        self.assertIn("truncated-abstract", self.codes(self.audit({"S": [paper]})))

    def test_duplicate_title_across_sections_is_an_error(self):
        second = dict(GOOD_PAPER, url="", abstract=GOOD_PAPER["abstract"] + " Different.")
        findings = self.audit({"A": [dict(GOOD_PAPER)], "B": [second]})
        self.assertIn("duplicate-title", self.codes(findings))

    def test_duplicate_abstract_is_an_error(self):
        second = dict(GOOD_PAPER, title="Another Paper", url="")
        self.assertIn("duplicate-abstract", self.codes(self.audit({"A": [dict(GOOD_PAPER), second]})))

    def test_invalid_url_is_an_error(self):
        paper = dict(GOOD_PAPER, pdf="ftp://bad.example/x.pdf")
        self.assertIn("invalid-url", self.codes(self.audit({"S": [paper]})))

    def test_unknown_field_is_an_error(self):
        paper = dict(GOOD_PAPER, sumary="typo field")
        self.assertIn("unknown-field", self.codes(self.audit({"S": [paper]})))

    def test_abstract_leaked_into_meta_is_an_error(self):
        paper = dict(GOOD_PAPER, meta="x" * 350)
        self.assertIn("abstract-in-meta", self.codes(self.audit({"S": [paper]})))

    def test_url_equal_to_pdf_is_a_warning(self):
        paper = dict(GOOD_PAPER, pdf=GOOD_PAPER["url"])
        finding = [f for f in self.audit({"S": [paper]}) if f.code == "url-equals-pdf"]
        self.assertEqual(len(finding), 1)
        self.assertEqual(finding[0].severity, "warning")


class AuditManifestChecks(AuditFixture):
    def test_orphan_section_file_is_an_error(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "sections").mkdir()
        (root / "sections" / "section-0.yaml").write_text(
            yaml.safe_dump([dict(GOOD_PAPER)], sort_keys=False), encoding="utf-8")
        (root / "sections" / "not-listed.yaml").write_text(
            yaml.safe_dump([dict(GOOD_PAPER, title="Other")], sort_keys=False),
            encoding="utf-8")
        (root / "sections.yaml").write_text(
            yaml.safe_dump({"sections": [
                {"file": "section-0.yaml", "title": "S", "on_homepage": True}]}),
            encoding="utf-8")

        loaded = load_sections(root)
        self.assertIn("orphan-section-file", self.codes(
            audit_content.audit_manifest(loaded, root)))

    def test_missing_section_file_raises(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "sections").mkdir()
        (root / "sections.yaml").write_text(
            yaml.safe_dump({"sections": [
                {"file": "gone.yaml", "title": "S", "on_homepage": True}]}),
            encoding="utf-8")
        with self.assertRaises((OSError, ValueError)):
            load_sections(root)


if __name__ == "__main__":
    unittest.main()
