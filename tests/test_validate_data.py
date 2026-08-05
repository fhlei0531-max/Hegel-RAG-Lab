import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_data import (
    validate_benchmark_record,
    validate_knowledge_text,
    validate_repository,
)


class KnowledgeValidationTests(unittest.TestCase):
    def test_accepts_valid_knowledge_card(self):
        text = """---
id: concept-recognition-001
type: concept
title: 承认
works: 精神现象学
review_status: drafted
version: 0.1.0
---

# 承认

教学性概括。
"""

        self.assertEqual(validate_knowledge_text(text, "recognition.md"), [])

    def test_rejects_knowledge_card_without_review_status(self):
        text = """---
id: concept-recognition-001
type: concept
title: 承认
works: 精神现象学
version: 0.1.0
---

# 承认
"""

        errors = validate_knowledge_text(text, "recognition.md")

        self.assertIn("recognition.md: missing frontmatter field 'review_status'", errors)


class BenchmarkValidationTests(unittest.TestCase):
    def setUp(self):
        self.valid_record = {
            "id": "concept-recognition-001",
            "category": "concept_explanation",
            "difficulty": "beginner",
            "question": "黑格尔所说的承认是什么意思？",
            "related_works": ["精神现象学"],
            "required_points": ["自我意识需要另一个自我意识"],
            "forbidden_errors": ["把承认等同于赞美"],
            "source_ids": ["concept-recognition-001"],
            "review_status": "drafted",
        }

    def test_accepts_valid_benchmark_item(self):
        self.assertEqual(
            validate_benchmark_record(self.valid_record, "development.jsonl:1"), []
        )

    def test_rejects_benchmark_item_without_forbidden_errors(self):
        record = dict(self.valid_record)
        del record["forbidden_errors"]

        errors = validate_benchmark_record(record, "development.jsonl:1")

        self.assertIn(
            "development.jsonl:1: missing benchmark field 'forbidden_errors'",
            errors,
        )


class RepositoryValidationTests(unittest.TestCase):
    def test_counts_valid_repository_data(self):
        knowledge = """---
id: concept-recognition-001
type: concept
title: 承认
works: 精神现象学
review_status: drafted
version: 0.1.0
---

# 承认
"""
        benchmark = {
            "id": "concept-recognition-001",
            "category": "concept_explanation",
            "difficulty": "beginner",
            "question": "黑格尔所说的承认是什么意思？",
            "related_works": ["精神现象学"],
            "required_points": ["自我意识需要另一个自我意识"],
            "forbidden_errors": ["把承认等同于赞美"],
            "source_ids": ["concept-recognition-001"],
            "review_status": "drafted",
        }

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            concept_directory = root / "data" / "knowledge" / "concepts"
            benchmark_directory = root / "data" / "benchmark"
            concept_directory.mkdir(parents=True)
            benchmark_directory.mkdir(parents=True)
            (concept_directory / "recognition.md").write_text(knowledge, encoding="utf-8")
            (benchmark_directory / "development.jsonl").write_text(
                json.dumps(benchmark, ensure_ascii=False) + "\n", encoding="utf-8"
            )

            knowledge_count, benchmark_count, errors = validate_repository(root)

        self.assertEqual((knowledge_count, benchmark_count), (1, 1))
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
