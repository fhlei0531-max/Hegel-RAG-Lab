import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "data" / "catalogs" / "hegel-core-concepts.json"
SCRIPT_PATH = ROOT / "scripts" / "generate_concept_hubs.py"


class ConceptCatalogTests(unittest.TestCase):
    def load_catalog(self):
        return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))

    def test_catalog_has_unique_complete_entries(self):
        catalog = self.load_catalog()
        entries = catalog["concepts"]

        self.assertEqual(len(entries), 150)
        self.assertEqual(len({entry["id"] for entry in entries}), len(entries))
        self.assertEqual(
            len({entry["filename"] for entry in entries}), len(entries)
        )
        for entry in entries:
            with self.subTest(entry=entry.get("id")):
                self.assertTrue(entry["id"].startswith("concept-"))
                self.assertTrue(entry["filename"].endswith(".md"))
                self.assertTrue(entry["preferred_label"].strip())
                self.assertTrue(entry["original_terms"])
                self.assertTrue(entry["candidate_contexts"])
                self.assertTrue(entry["verification_questions"])

    def test_catalog_filenames_match_concept_ids(self):
        entries = self.load_catalog()["concepts"]

        for entry in entries:
            with self.subTest(entry=entry["id"]):
                self.assertEqual(
                    entry["filename"], entry["id"].removeprefix("concept-") + ".md"
                )

    def test_related_concepts_reference_catalog_entries(self):
        entries = self.load_catalog()["concepts"]
        ids = {entry["id"] for entry in entries}

        for entry in entries:
            for related_id in entry.get("related_concept_ids", []):
                with self.subTest(entry=entry["id"], related_id=related_id):
                    self.assertIn(related_id, ids)
                    self.assertNotEqual(related_id, entry["id"])

    def test_catalog_does_not_mix_in_reception_labels(self):
        ids = {entry["id"] for entry in self.load_catalog()["concepts"]}

        self.assertNotIn("concept-historicism", ids)


class ConceptHubGeneratorTests(unittest.TestCase):
    def run_generator(self, output: Path, *extra_args: str):
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--catalog",
                str(CATALOG_PATH),
                "--output",
                str(output),
                *extra_args,
            ],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )

    def test_generates_drafted_hubs_without_source_claims(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory)

            result = self.run_generator(output)

            self.assertEqual(result.returncode, 0, result.stderr)
            card = output / "being.md"
            text = card.read_text(encoding="utf-8")
            self.assertIn("id: concept-being", text)
            self.assertIn("type: concept_hub", text)
            self.assertIn("context_ids: []", text)
            self.assertIn("review_status: drafted", text)
            self.assertIn("## 候选语境（待核验）", text)
            self.assertNotIn("passage_locator", text)
            self.assertNotIn("source_checked", text)

    def test_does_not_overwrite_an_existing_card(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory)
            existing = output / "being.md"
            existing.write_text("human revision\n", encoding="utf-8")

            result = self.run_generator(output)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(existing.read_text(encoding="utf-8"), "human revision\n")

    def test_check_does_not_accept_a_card_with_the_wrong_id(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory)
            first_run = self.run_generator(output)
            self.assertEqual(first_run.returncode, 0, first_run.stderr)
            (output / "being.md").write_text(
                "---\nid: concept-wrong\ntype: concept_hub\n---\n", encoding="utf-8"
            )

            result = self.run_generator(output, "--check")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Mismatched", result.stdout)

    def test_check_reports_frontmatter_drift(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory)
            first_run = self.run_generator(output)
            self.assertEqual(first_run.returncode, 0, first_run.stderr)
            card = output / "being.md"
            card.write_text(
                card.read_text(encoding="utf-8").replace(
                    "review_status: drafted", "review_status: published"
                ),
                encoding="utf-8",
            )

            result = self.run_generator(output, "--check")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Drifted", result.stdout)

    def test_check_reports_missing_cards(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory)

            result = self.run_generator(output, "--check")

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Missing", result.stdout)


if __name__ == "__main__":
    unittest.main()
