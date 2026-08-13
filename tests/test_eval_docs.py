import re
import tempfile
import unittest
from pathlib import Path

from scripts.validate_data import validate_knowledge_text, validate_repository


ROOT = Path(__file__).resolve().parents[1]
RUBRIC = ROOT / "eval" / "rubric.md"
REVIEW_FORM = ROOT / "eval" / "review-form.md"


class EvaluationDocumentationTests(unittest.TestCase):
    def review_record_example(self) -> str:
        text = REVIEW_FORM.read_text(encoding="utf-8")
        marker = "```yaml\n"
        start = text.index(marker) + len(marker)
        end = text.index("\n```", start)
        example = text[start:end]
        example = example.replace(
            "review-<entity-slug>-<sequence>", "review-work-example-001"
        )
        example = re.sub(r"title: <[^>]+>", "title: Example work review", example)
        example = re.sub(
            r"reviewed_entity_id: <[^>]+>",
            "reviewed_entity_id: work-example",
            example,
        )
        example = re.sub(
            r"reviewer_alias: <[^>]+>", "reviewer_alias: reviewer-01", example
        )
        return example.replace("YYYY-MM-DD", "2026-08-13")

    def test_review_form_example_passes_record_validation(self):
        self.assertEqual(
            validate_knowledge_text(self.review_record_example(), "review.md"), []
        )

    def test_review_form_example_links_to_reviewed_entity(self):
        work = """---
id: work-example
type: work
title: Example Work
original_title: Example Work
author: Example Author
original_language: de
review_status: source_checked
version: 0.1.0
review_ids: ["review-work-example-001"]
---
"""

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            work_path = root / "data/knowledge/works/example.md"
            review_path = root / "data/knowledge/reviews/example.md"
            work_path.parent.mkdir(parents=True)
            review_path.parent.mkdir(parents=True)
            work_path.write_text(work, encoding="utf-8")
            review_path.write_text(self.review_record_example(), encoding="utf-8")

            _, _, errors = validate_repository(root)

        self.assertEqual(errors, [])

    def test_review_form_contains_machine_readable_review_record_skeleton(self):
        text = REVIEW_FORM.read_text(encoding="utf-8")

        self.assertIn("type: review_record", text)
        self.assertIn("reviewed_entity_id:", text)
        self.assertIn("reviewer_alias:", text)
        self.assertIn("review_date:", text)
        self.assertIn("review_status: source_checked", text)

    def test_content_and_agent_scoring_remain_separate(self):
        rubric = RUBRIC.read_text(encoding="utf-8")
        review_form = REVIEW_FORM.read_text(encoding="utf-8")

        self.assertIn("\u53ea\u8bc4\u4f30 Agent \u7684\u539f\u59cb\u56de\u7b54", rubric)
        self.assertIn("\u4e0d\u80fd\u5148\u7531\u4eba\u4fee\u8ba2\u7b54\u6848", rubric)
        self.assertIn("concept_hub", review_form)
        self.assertIn("contextual_sense", review_form)
        self.assertIn("source_locator", review_form)
        self.assertIn("claim", review_form)

    def test_review_form_documents_source_checked_audit_requirement(self):
        text = REVIEW_FORM.read_text(encoding="utf-8")

        self.assertIn("\u4ece `drafted` \u664b\u7ea7\u5230 `source_checked`", text)
        self.assertIn("review_ids", text)

    def test_review_form_distinguishes_review_and_locator_statuses(self):
        text = REVIEW_FORM.read_text(encoding="utf-8")

        self.assertIn("`review_status` \u4e0e `locator_status`", text)
        self.assertIn("`edition_checked`", text)
        self.assertIn("`passage_checked`", text)

    def test_review_form_keeps_contextless_concept_hubs_drafted(self):
        text = REVIEW_FORM.read_text(encoding="utf-8")

        self.assertIn(
            "\u6ca1\u6709\u8bed\u5883\u4e49\u9879\u7684\u7eaf\u76ee\u5f55\u5165\u53e3\u4fdd\u6301 `drafted`",
            text,
        )

    def test_second_review_allows_justified_not_applicable_items(self):
        text = REVIEW_FORM.read_text(encoding="utf-8")

        self.assertIn(
            "\u5176\u4f59\u5747\u4e3a `no` \u6216\u5df2\u8bf4\u660e\u7406\u7531\u7684 `N/A`",
            text,
        )

    def test_rubric_separates_recall_from_contamination(self):
        text = RUBRIC.read_text(encoding="utf-8")

        self.assertIn(
            "\u53ec\u56de\u7a0b\u5ea6\uff1a`hit / partial_hit / miss`", text
        )
        self.assertIn(
            "\u6c61\u67d3\u60c5\u51b5\uff1a`none / wrong_context / answer_leakage / other`",
            text,
        )


if __name__ == "__main__":
    unittest.main()
