from __future__ import annotations

import json
from pathlib import Path
from typing import Any


KNOWLEDGE_REQUIRED_FIELDS = (
    "id",
    "type",
    "title",
    "works",
    "review_status",
    "version",
)

BENCHMARK_REQUIRED_FIELDS = (
    "id",
    "category",
    "difficulty",
    "question",
    "related_works",
    "required_points",
    "forbidden_errors",
    "source_ids",
    "review_status",
)


def parse_frontmatter(text: str) -> dict[str, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()
    return {}


def validate_knowledge_text(text: str, source: str) -> list[str]:
    fields = parse_frontmatter(text)
    if not fields:
        return [f"{source}: missing or invalid frontmatter"]

    return [
        f"{source}: missing frontmatter field '{field}'"
        for field in KNOWLEDGE_REQUIRED_FIELDS
        if not fields.get(field)
    ]


def validate_benchmark_record(record: dict[str, Any], source: str) -> list[str]:
    return [
        f"{source}: missing benchmark field '{field}'"
        for field in BENCHMARK_REQUIRED_FIELDS
        if field not in record or record[field] in (None, "", [])
    ]


def validate_repository(root: Path) -> tuple[int, int, list[str]]:
    errors: list[str] = []
    knowledge_count = 0
    benchmark_count = 0

    knowledge_root = root / "data" / "knowledge"
    if knowledge_root.exists():
        for path in sorted(knowledge_root.rglob("*.md")):
            knowledge_count += 1
            errors.extend(
                validate_knowledge_text(
                    path.read_text(encoding="utf-8"),
                    str(path.relative_to(root)),
                )
            )

    benchmark_root = root / "data" / "benchmark"
    if benchmark_root.exists():
        for path in sorted(benchmark_root.glob("*.jsonl")):
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if not line.strip():
                    continue
                source = f"{path.relative_to(root)}:{line_number}"
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as error:
                    errors.append(f"{source}: invalid JSON ({error.msg})")
                    continue
                benchmark_count += 1
                errors.extend(validate_benchmark_record(record, source))

    return knowledge_count, benchmark_count, errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    knowledge_count, benchmark_count, errors = validate_repository(root)

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(
        f"Validated {knowledge_count} knowledge file(s) "
        f"and {benchmark_count} benchmark item(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
