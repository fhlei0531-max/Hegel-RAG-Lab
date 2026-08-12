import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_data import (
    parse_frontmatter,
    validate_benchmark_record,
    validate_claim_record,
    validate_interpretation_record,
    validate_knowledge_text,
    validate_repository,
)


CONCEPT_HUB = """---
id: concept-recognition
type: concept_hub
title: 承认
preferred_label: 承认
original_terms: [{"language": "de", "value": "Anerkennung"}]
context_ids: ["context-recognition-phenomenology"]
review_status: drafted
version: 0.2.0
---

# 承认
"""

WORK = """---
id: work-phenomenology-of-spirit
type: work
title: 精神现象学
original_title: Phänomenologie des Geistes
author: Georg Wilhelm Friedrich Hegel
original_language: de
review_status: source_checked
version: 0.2.0
---

# 精神现象学
"""

PUBLICATION = """---
id: publication-example
type: publication
title: 已核验的二手研究示例
authors: ["Researcher A"]
publication_year: 2020
stable_identifier: "doi:10.0000/example"
full_text_status: full_text_checked
review_status: source_checked
version: 0.2.0
---

# 二手研究元数据
"""

CONTEXTUAL_SENSE = """---
id: context-recognition-phenomenology
type: contextual_sense
title: 《精神现象学》自我意识语境中的承认
concept_id: concept-recognition
work_id: work-phenomenology-of-spirit
section: 自我意识
source_ids: ["source-phenomenology-self-consciousness"]
review_status: drafted
version: 0.2.0
---

# 语境义项
"""

SOURCE_LOCATOR = """---
id: source-phenomenology-self-consciousness
type: source_locator
title: 《精神现象学》自我意识部分
work_id: work-phenomenology-of-spirit
section: 自我意识
edition: to_select
passage_locator: to_verify
locator_status: to_verify
review_status: drafted
version: 0.2.0
---

# 来源定位
"""


def valid_claim() -> dict:
    return {
        "id": "claim-recognition-001",
        "type": "claim",
        "text": "承认涉及自我意识之间的关系。",
        "claim_type": "editorial_summary",
        "context_id": "context-recognition-phenomenology",
        "evidence_ids": ["source-phenomenology-self-consciousness"],
        "support_status": "to_verify",
        "review_status": "drafted",
    }


def valid_benchmark() -> dict:
    return {
        "id": "bench-recognition-001",
        "category": "concept_explanation",
        "difficulty": "beginner",
        "question": "黑格尔所说的承认是什么意思？",
        "related_works": ["work-phenomenology-of-spirit"],
        "required_points": ["承认涉及自我意识之间的关系"],
        "forbidden_errors": ["把承认等同于赞美"],
        "claim_ids": ["claim-recognition-001"],
        "review_status": "drafted",
    }


class FrontmatterTests(unittest.TestCase):
    def test_parses_json_arrays_as_typed_values(self):
        fields = parse_frontmatter(CONCEPT_HUB)

        self.assertEqual(fields["context_ids"], ["context-recognition-phenomenology"])
        self.assertEqual(
            fields["original_terms"],
            [{"language": "de", "value": "Anerkennung"}],
        )

    def test_parses_numeric_json_scalars(self):
        fields = parse_frontmatter(PUBLICATION)

        self.assertEqual(fields["publication_year"], 2020)


class KnowledgeValidationTests(unittest.TestCase):
    def test_accepts_valid_contextual_entities(self):
        for name, text in (
            ("work.md", WORK),
            ("concept.md", CONCEPT_HUB),
            ("context.md", CONTEXTUAL_SENSE),
            ("source.md", SOURCE_LOCATOR),
        ):
            with self.subTest(name=name):
                self.assertEqual(validate_knowledge_text(text, name), [])

    def test_rejects_concept_hub_without_context_ids(self):
        text = CONCEPT_HUB.replace(
            'context_ids: ["context-recognition-phenomenology"]\n', ""
        )

        errors = validate_knowledge_text(text, "concept.md")

        self.assertIn("concept.md: missing frontmatter field 'context_ids'", errors)

    def test_accepts_drafted_concept_hub_with_empty_context_ids(self):
        text = CONCEPT_HUB.replace(
            'context_ids: ["context-recognition-phenomenology"]',
            "context_ids: []",
        )

        errors = validate_knowledge_text(text, "concept.md")

        self.assertEqual(errors, [])

    def test_rejects_unknown_review_status(self):
        text = CONCEPT_HUB.replace("review_status: drafted", "review_status: approved")

        errors = validate_knowledge_text(text, "concept.md")

        self.assertIn("concept.md: invalid review_status 'approved'", errors)

    def test_rejects_string_where_context_id_array_is_required(self):
        text = CONCEPT_HUB.replace(
            'context_ids: ["context-recognition-phenomenology"]',
            "context_ids: context-recognition-phenomenology",
        )

        errors = validate_knowledge_text(text, "concept.md")

        self.assertIn("concept.md: field 'context_ids' must be list[str]", errors)

    def test_rejects_invalid_common_field_types(self):
        text = WORK.replace(
            "original_title: Phänomenologie des Geistes",
            'original_title: ["Phänomenologie des Geistes"]',
        )

        errors = validate_knowledge_text(text, "work.md")

        self.assertIn("work.md: field 'original_title' must be str", errors)

    def test_rejects_published_content_without_review_ids(self):
        text = CONCEPT_HUB.replace("review_status: drafted", "review_status: published")

        errors = validate_knowledge_text(text, "concept.md")

        self.assertIn(
            "concept.md: review_status 'published' requires non-empty review_ids",
            errors,
        )

    def test_rejects_source_checked_concept_without_review_ids(self):
        text = CONCEPT_HUB.replace(
            "review_status: drafted", "review_status: source_checked"
        )

        errors = validate_knowledge_text(text, "concept.md")

        self.assertIn(
            "concept.md: review_status 'source_checked' requires non-empty review_ids",
            errors,
        )

    def test_rejects_passage_checked_source_with_placeholder_locator(self):
        text = SOURCE_LOCATOR.replace(
            "locator_status: to_verify", "locator_status: passage_checked"
        )

        errors = validate_knowledge_text(text, "source.md")

        self.assertIn(
            "source.md: passage_checked requires verified edition and passage_locator",
            errors,
        )


class ClaimValidationTests(unittest.TestCase):
    def test_accepts_valid_claim(self):
        self.assertEqual(validate_claim_record(valid_claim(), "claims.jsonl:1"), [])

    def test_rejects_unknown_claim_type(self):
        record = valid_claim()
        record["claim_type"] = "objective_truth"

        errors = validate_claim_record(record, "claims.jsonl:1")

        self.assertIn(
            "claims.jsonl:1: invalid claim_type 'objective_truth'", errors
        )

    def test_rejects_claim_with_empty_evidence_ids(self):
        record = valid_claim()
        record["evidence_ids"] = []

        errors = validate_claim_record(record, "claims.jsonl:1")

        self.assertIn(
            "claims.jsonl:1: missing claim field 'evidence_ids'", errors
        )

    def test_rejects_non_object_claim(self):
        errors = validate_claim_record([], "claims.jsonl:1")

        self.assertIn("claims.jsonl:1: record must be a JSON object", errors)


class InterpretationValidationTests(unittest.TestCase):
    def test_accepts_valid_interpretation(self):
        record = {
            "id": "interpretation-recognition-001",
            "type": "interpretation",
            "publication_id": "publication-example",
            "claim_id": "claim-recognition-001",
            "position": "qualifies",
            "evidence_locator": "p. 10",
            "review_status": "drafted",
        }

        self.assertEqual(
            validate_interpretation_record(record, "interpretations.jsonl:1"), []
        )

    def test_rejects_interpretation_without_evidence_locator(self):
        record = {
            "id": "interpretation-recognition-001",
            "type": "interpretation",
            "publication_id": "publication-example",
            "claim_id": "claim-recognition-001",
            "position": "qualifies",
            "review_status": "drafted",
        }

        errors = validate_interpretation_record(record, "interpretations.jsonl:1")

        self.assertIn(
            "interpretations.jsonl:1: missing interpretation field 'evidence_locator'",
            errors,
        )

    def test_rejects_placeholder_evidence_locator(self):
        record = {
            "id": "interpretation-recognition-001",
            "type": "interpretation",
            "publication_id": "publication-example",
            "claim_id": "claim-recognition-001",
            "position": "qualifies",
            "evidence_locator": "to_verify",
            "review_status": "drafted",
        }

        errors = validate_interpretation_record(record, "interpretations.jsonl:1")

        self.assertIn(
            "interpretations.jsonl:1: evidence_locator must be verified", errors
        )


class BenchmarkValidationTests(unittest.TestCase):
    def test_accepts_valid_benchmark_item(self):
        self.assertEqual(
            validate_benchmark_record(valid_benchmark(), "development.jsonl:1"),
            [],
        )

    def test_rejects_benchmark_without_claim_ids(self):
        record = valid_benchmark()
        del record["claim_ids"]

        errors = validate_benchmark_record(record, "development.jsonl:1")

        self.assertIn(
            "development.jsonl:1: missing benchmark field 'claim_ids'", errors
        )

    def test_rejects_unknown_difficulty_and_string_required_points(self):
        record = valid_benchmark()
        record["difficulty"] = "expert"
        record["required_points"] = "一个要点"

        errors = validate_benchmark_record(record, "development.jsonl:1")

        self.assertIn("development.jsonl:1: invalid difficulty 'expert'", errors)
        self.assertIn(
            "development.jsonl:1: field 'required_points' must be list[str]", errors
        )


class RepositoryValidationTests(unittest.TestCase):
    def write_valid_repository(self, root: Path) -> None:
        files = {
            "data/knowledge/works/phenomenology-of-spirit.md": WORK,
            "data/knowledge/publications/example.md": PUBLICATION,
            "data/knowledge/concepts/recognition.md": CONCEPT_HUB,
            "data/knowledge/contexts/recognition.md": CONTEXTUAL_SENSE,
            "data/knowledge/sources/recognition.md": SOURCE_LOCATOR,
        }
        for relative_path, text in files.items():
            path = root / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

        claims = root / "data/knowledge/claims/recognition.jsonl"
        claims.parent.mkdir(parents=True, exist_ok=True)
        claims.write_text(
            json.dumps(valid_claim(), ensure_ascii=False) + "\n", encoding="utf-8"
        )

        benchmark = root / "data/benchmark/development.jsonl"
        benchmark.parent.mkdir(parents=True, exist_ok=True)
        benchmark.write_text(
            json.dumps(valid_benchmark(), ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def test_counts_connected_repository_data(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.write_valid_repository(root)

            knowledge_count, benchmark_count, errors = validate_repository(root)

        self.assertEqual((knowledge_count, benchmark_count), (6, 1))
        self.assertEqual(errors, [])

    def test_rejects_duplicate_ids(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.write_valid_repository(root)
            duplicate = root / "data/knowledge/concepts/duplicate.md"
            duplicate.write_text(CONCEPT_HUB, encoding="utf-8")

            _, _, errors = validate_repository(root)

        self.assertTrue(
            any("duplicate entity id 'concept-recognition'" in error for error in errors),
            errors,
        )

    def test_rejects_duplicate_benchmark_ids(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.write_valid_repository(root)
            benchmark = root / "data/benchmark/development.jsonl"
            line = benchmark.read_text(encoding="utf-8")
            benchmark.write_text(line + line, encoding="utf-8")

            _, _, errors = validate_repository(root)

        self.assertTrue(
            any("duplicate entity id 'bench-recognition-001'" in error for error in errors),
            errors,
        )

    def test_rejects_broken_references(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.write_valid_repository(root)
            concept = root / "data/knowledge/concepts/recognition.md"
            concept.write_text(
                CONCEPT_HUB.replace(
                    "context-recognition-phenomenology", "context-does-not-exist"
                ),
                encoding="utf-8",
            )

            _, _, errors = validate_repository(root)

        self.assertTrue(
            any("references missing id 'context-does-not-exist'" in error for error in errors),
            errors,
        )

    def test_rejects_reference_to_wrong_entity_type(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.write_valid_repository(root)
            claim_path = root / "data/knowledge/claims/recognition.jsonl"
            record = valid_claim()
            record["evidence_ids"] = ["concept-recognition"]
            claim_path.write_text(
                json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8"
            )

            _, _, errors = validate_repository(root)

        self.assertTrue(
            any("field 'evidence_ids' must reference type 'source_locator'" in error for error in errors),
            errors,
        )

    def test_rejects_context_that_does_not_link_back_to_concept(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.write_valid_repository(root)
            context_path = root / "data/knowledge/contexts/recognition.md"
            context_path.write_text(
                CONTEXTUAL_SENSE.replace(
                    "concept_id: concept-recognition", "concept_id: publication-example"
                ),
                encoding="utf-8",
            )

            _, _, errors = validate_repository(root)

        self.assertTrue(
            any("field 'concept_id' must reference type 'concept_hub'" in error for error in errors),
            errors,
        )

    def test_rejects_concept_context_pair_with_mismatched_backlink(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.write_valid_repository(root)
            second_concept = root / "data/knowledge/concepts/second.md"
            second_concept.write_text(
                CONCEPT_HUB.replace("concept-recognition", "concept-second").replace(
                    'context_ids: ["context-recognition-phenomenology"]',
                    'context_ids: ["context-recognition-phenomenology"]',
                ),
                encoding="utf-8",
            )

            _, _, errors = validate_repository(root)

        self.assertTrue(
            any("context backlink points to 'concept-recognition'" in error for error in errors),
            errors,
        )

    def test_reports_non_object_jsonl_record_without_crashing(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.write_valid_repository(root)
            claim_path = root / "data/knowledge/claims/recognition.jsonl"
            claim_path.write_text("[]\n", encoding="utf-8")

            _, _, errors = validate_repository(root)

        self.assertIn(
            "data\\knowledge\\claims\\recognition.jsonl:1: record must be a JSON object",
            errors,
        )

    def test_reports_invalid_reference_field_type_without_crashing(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.write_valid_repository(root)
            concept_path = root / "data/knowledge/concepts/recognition.md"
            concept_path.write_text(
                CONCEPT_HUB.replace(
                    'context_ids: ["context-recognition-phenomenology"]',
                    "context_ids: 42",
                ),
                encoding="utf-8",
            )

            _, _, errors = validate_repository(root)

        self.assertIn(
            "data\\knowledge\\concepts\\recognition.md: field 'context_ids' must be list[str]",
            errors,
        )

    def test_rejects_review_record_for_another_entity(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.write_valid_repository(root)
            review_path = root / "data/knowledge/reviews/concept-review.md"
            review_path.parent.mkdir(parents=True, exist_ok=True)
            review_path.write_text(
                """---
id: review-concept-001
type: review_record
title: 概念审核记录
reviewed_entity_id: claim-recognition-001
reviewer_alias: reviewer-01
review_date: 2026-08-13
review_status: source_checked
version: 0.1.0
---
""",
                encoding="utf-8",
            )
            concept_path = root / "data/knowledge/concepts/recognition.md"
            concept_path.write_text(
                CONCEPT_HUB.replace(
                    "review_status: drafted",
                    'review_status: published\nreview_ids: ["review-concept-001"]',
                ),
                encoding="utf-8",
            )

            _, _, errors = validate_repository(root)

        self.assertTrue(
            any("review record belongs to 'claim-recognition-001'" in error for error in errors),
            errors,
        )

    def test_rejects_unlisted_context_backlink(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.write_valid_repository(root)
            extra_context = root / "data/knowledge/contexts/extra.md"
            extra_context.write_text(
                CONTEXTUAL_SENSE.replace(
                    "context-recognition-phenomenology", "context-extra"
                ),
                encoding="utf-8",
            )

            _, _, errors = validate_repository(root)

        self.assertTrue(
            any("is not listed in concept 'concept-recognition' context_ids" in error for error in errors),
            errors,
        )

    def test_rejects_context_source_from_another_work(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.write_valid_repository(root)
            second_work = root / "data/knowledge/works/second.md"
            second_work.write_text(
                WORK.replace("work-phenomenology-of-spirit", "work-second"),
                encoding="utf-8",
            )
            source_path = root / "data/knowledge/sources/recognition.md"
            source_path.write_text(
                SOURCE_LOCATOR.replace(
                    "work-phenomenology-of-spirit", "work-second"
                ),
                encoding="utf-8",
            )

            _, _, errors = validate_repository(root)

        self.assertTrue(
            any("source work 'work-second' does not match context work" in error for error in errors),
            errors,
        )

    def test_rejects_claim_evidence_from_another_context_work(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.write_valid_repository(root)
            second_work = root / "data/knowledge/works/second.md"
            second_work.write_text(
                WORK.replace("work-phenomenology-of-spirit", "work-second"),
                encoding="utf-8",
            )
            second_source = root / "data/knowledge/sources/second.md"
            second_source.write_text(
                SOURCE_LOCATOR.replace(
                    "source-phenomenology-self-consciousness", "source-second"
                ).replace("work-phenomenology-of-spirit", "work-second"),
                encoding="utf-8",
            )
            claim_path = root / "data/knowledge/claims/recognition.jsonl"
            record = valid_claim()
            record["evidence_ids"] = ["source-second"]
            claim_path.write_text(
                json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8"
            )

            _, _, errors = validate_repository(root)

        self.assertTrue(
            any("evidence work 'work-second' does not match context work" in error for error in errors),
            errors,
        )

    def test_rejects_edition_checked_placeholder_edition(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.write_valid_repository(root)
            source_path = root / "data/knowledge/sources/recognition.md"
            source_path.write_text(
                SOURCE_LOCATOR.replace(
                    "locator_status: to_verify", "locator_status: edition_checked"
                ),
                encoding="utf-8",
            )

            _, _, errors = validate_repository(root)

        self.assertTrue(
            any("edition_checked requires verified edition" in error for error in errors),
            errors,
        )

    def test_rejects_source_supported_claim_with_unverified_source(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.write_valid_repository(root)
            claim_path = root / "data/knowledge/claims/recognition.jsonl"
            record = valid_claim()
            record["support_status"] = "source_supported"
            claim_path.write_text(
                json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8"
            )

            _, _, errors = validate_repository(root)

        self.assertTrue(
            any("source_supported requires passage_checked evidence" in error for error in errors),
            errors,
        )

    def test_rejects_published_record_with_missing_review_record(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.write_valid_repository(root)
            concept_path = root / "data/knowledge/concepts/recognition.md"
            concept_path.write_text(
                CONCEPT_HUB.replace(
                    "review_status: drafted",
                    'review_status: published\nreview_ids: ["review-does-not-exist"]',
                ),
                encoding="utf-8",
            )

            _, _, errors = validate_repository(root)

        self.assertTrue(
            any("references missing id 'review-does-not-exist'" in error for error in errors),
            errors,
        )

    def test_rejects_interpretation_when_publication_body_is_not_checked(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.write_valid_repository(root)
            publication_path = root / "data/knowledge/publications/example.md"
            publication_path.write_text(
                PUBLICATION.replace("full_text_checked", "metadata_only"),
                encoding="utf-8",
            )
            interpretation_path = root / "data/knowledge/interpretations/example.jsonl"
            interpretation_path.parent.mkdir(parents=True, exist_ok=True)
            interpretation_path.write_text(
                json.dumps(
                    {
                        "id": "interpretation-recognition-001",
                        "type": "interpretation",
                        "publication_id": "publication-example",
                        "claim_id": "claim-recognition-001",
                        "position": "qualifies",
                        "evidence_locator": "p. 10",
                        "review_status": "drafted",
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            _, _, errors = validate_repository(root)

        self.assertTrue(
            any("interpretation requires full_text_checked publication" in error for error in errors),
            errors,
        )

    def test_rejects_missing_work_reference(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.write_valid_repository(root)
            (root / "data/knowledge/works/phenomenology-of-spirit.md").unlink()

            _, _, errors = validate_repository(root)

        self.assertTrue(
            any("references missing id 'work-phenomenology-of-spirit'" in error for error in errors),
            errors,
        )

    def test_rejects_missing_benchmark_work_reference(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            self.write_valid_repository(root)
            (root / "data/knowledge/works/phenomenology-of-spirit.md").unlink()

            _, _, errors = validate_repository(root)

        benchmark_errors = [
            error for error in errors if error.startswith("data\\benchmark")
        ]
        self.assertTrue(
            any("references missing id 'work-phenomenology-of-spirit'" in error for error in benchmark_errors),
            errors,
        )


if __name__ == "__main__":
    unittest.main()
