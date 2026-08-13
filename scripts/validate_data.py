from __future__ import annotations

import json
from pathlib import Path
from typing import Any


BASE_KNOWLEDGE_REQUIRED_FIELDS = (
    "id",
    "type",
    "title",
    "review_status",
    "version",
)

KNOWLEDGE_TYPE_FIELDS = {
    "work": ("original_title", "author", "original_language"),
    "publication": (
        "authors",
        "publication_year",
        "stable_identifier",
        "full_text_status",
    ),
    "review_record": ("reviewed_entity_id", "reviewer_alias", "review_date"),
    "concept_hub": ("preferred_label", "original_terms", "context_ids"),
    "contextual_sense": (
        "concept_id",
        "work_id",
        "section",
        "source_ids",
    ),
    "source_locator": (
        "work_id",
        "section",
        "edition",
        "passage_locator",
        "locator_status",
    ),
}

CLAIM_REQUIRED_FIELDS = (
    "id",
    "type",
    "text",
    "claim_type",
    "context_id",
    "evidence_ids",
    "support_status",
    "review_status",
)

INTERPRETATION_REQUIRED_FIELDS = (
    "id",
    "type",
    "publication_id",
    "claim_id",
    "position",
    "evidence_locator",
    "review_status",
)

BENCHMARK_REQUIRED_FIELDS = (
    "id",
    "category",
    "difficulty",
    "question",
    "related_works",
    "required_points",
    "forbidden_errors",
    "claim_ids",
    "review_status",
)

REVIEW_STATUSES = {
    "drafted",
    "source_checked",
    "philosophy_reviewed",
    "published",
}

LOCATOR_STATUSES = {"to_verify", "edition_checked", "passage_checked"}

CLAIM_TYPES = {
    "textual_fact",
    "paraphrase",
    "editorial_summary",
    "scholarly_interpretation",
    "pedagogical_explanation",
    "analogy",
}

SUPPORT_STATUSES = {"to_verify", "source_supported", "contested", "unsupported"}
INTERPRETATION_POSITIONS = {"supports", "qualifies", "rejects"}
DIFFICULTIES = {"beginner", "intermediate", "advanced"}
FULL_TEXT_STATUSES = {"metadata_only", "full_text_checked"}

LIST_STRING_FIELDS = {
    "authors",
    "context_ids",
    "related_concept_ids",
    "source_ids",
    "evidence_ids",
    "claim_ids",
    "related_works",
    "required_points",
    "forbidden_errors",
    "review_ids",
}

STRING_FIELDS = {
    "id",
    "type",
    "title",
    "original_title",
    "author",
    "original_language",
    "stable_identifier",
    "category",
    "review_status",
    "version",
    "preferred_label",
    "concept_id",
    "work_id",
    "publication_id",
    "claim_id",
    "section",
    "locator_status",
    "text",
    "claim_type",
    "context_id",
    "support_status",
    "position",
    "difficulty",
    "question",
    "edition",
    "passage_locator",
    "evidence_locator",
    "full_text_status",
    "reviewed_entity_id",
    "reviewer_alias",
    "review_date",
}

REFERENCE_TARGET_TYPES = {
    "work_id": {"work"},
    "related_works": {"work"},
    "publication_id": {"publication"},
    "concept_id": {"concept_hub"},
    "context_id": {"contextual_sense"},
    "context_ids": {"contextual_sense"},
    "source_ids": {"source_locator"},
    "evidence_ids": {"source_locator"},
    "claim_id": {"claim"},
    "claim_ids": {"claim"},
    "review_ids": {"review_record"},
    "reviewed_entity_id": {
        "work",
        "publication",
        "concept_hub",
        "contextual_sense",
        "source_locator",
        "claim",
        "interpretation",
        "benchmark",
    },
}

REFERENCE_FIELDS = {
    "work_id",
    "publication_id",
    "concept_id",
    "context_id",
    "claim_id",
    "context_ids",
    "source_ids",
    "evidence_ids",
    "claim_ids",
    "related_works",
    "review_ids",
    "reviewed_entity_id",
}


def _parse_frontmatter_value(value: str) -> Any:
    value = value.strip()
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def parse_frontmatter(text: str) -> dict[str, Any]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    fields: dict[str, Any] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = _parse_frontmatter_value(value)
    return {}


def _missing_field_errors(
    record: dict[str, Any], required_fields: tuple[str, ...], source: str, label: str
) -> list[str]:
    return [
        f"{source}: missing {label} field '{field}'"
        for field in required_fields
        if field not in record
        or record[field] in (None, "")
        or (
            record[field] == []
            and not (
                record.get("type") == "concept_hub"
                and field == "context_ids"
                and record.get("review_status") == "drafted"
            )
        )
    ]


def _enum_error(
    record: dict[str, Any], field: str, allowed: set[str], source: str
) -> list[str]:
    value = record.get(field)
    if value is None:
        return []
    if isinstance(value, str) and value in allowed:
        return []
    return [f"{source}: invalid {field} '{value}'"]


def _type_errors(record: dict[str, Any], source: str) -> list[str]:
    errors: list[str] = []
    for field in STRING_FIELDS:
        if field in record and not isinstance(record[field], str):
            errors.append(f"{source}: field '{field}' must be str")
    for field in LIST_STRING_FIELDS:
        if field in record and not (
            isinstance(record[field], list)
            and all(isinstance(item, str) for item in record[field])
        ):
            errors.append(f"{source}: field '{field}' must be list[str]")
    if "original_terms" in record:
        terms = record["original_terms"]
        valid_terms = isinstance(terms, list) and all(
            isinstance(term, dict)
            and isinstance(term.get("language"), str)
            and isinstance(term.get("value"), str)
            for term in terms
        )
        if not valid_terms:
            errors.append(
                f"{source}: field 'original_terms' must be list[language/value object]"
            )
    if "publication_year" in record and not isinstance(
        record["publication_year"], int
    ):
        errors.append(f"{source}: field 'publication_year' must be int")
    return errors


def _require_object(record: Any, source: str) -> list[str]:
    if isinstance(record, dict):
        return []
    return [f"{source}: record must be a JSON object"]


def _review_state_errors(record: dict[str, Any], source: str) -> list[str]:
    status = record.get("review_status")
    entity_type = record.get("type")
    requires_review = status in {"philosophy_reviewed", "published"} or (
        status == "source_checked"
        and entity_type
        in {"concept_hub", "contextual_sense", "source_locator", "claim", "benchmark"}
    )
    if not requires_review:
        return []
    review_ids = record.get("review_ids")
    if isinstance(review_ids, list) and review_ids and all(
        isinstance(item, str) for item in review_ids
    ):
        return []
    return [
        f"{source}: review_status '{record.get('review_status')}' "
        "requires non-empty review_ids"
    ]


def validate_knowledge_text(text: str, source: str) -> list[str]:
    fields = parse_frontmatter(text)
    if not fields:
        return [f"{source}: missing or invalid frontmatter"]

    errors = _missing_field_errors(
        fields, BASE_KNOWLEDGE_REQUIRED_FIELDS, source, "frontmatter"
    )
    errors.extend(_type_errors(fields, source))
    entity_type = fields.get("type")
    if entity_type not in KNOWLEDGE_TYPE_FIELDS:
        if entity_type:
            errors.append(f"{source}: invalid type '{entity_type}'")
        return errors

    errors.extend(
        _missing_field_errors(
            fields, KNOWLEDGE_TYPE_FIELDS[entity_type], source, "frontmatter"
        )
    )
    errors.extend(_enum_error(fields, "review_status", REVIEW_STATUSES, source))
    errors.extend(_review_state_errors(fields, source))
    if entity_type == "source_locator":
        errors.extend(_enum_error(fields, "locator_status", LOCATOR_STATUSES, source))
        if fields.get("locator_status") == "passage_checked" and (
            fields.get("edition") in {None, "", "to_select"}
            or fields.get("passage_locator") in {None, "", "to_verify"}
        ):
            errors.append(
                f"{source}: passage_checked requires verified edition and passage_locator"
            )
        if fields.get("locator_status") == "edition_checked" and fields.get(
            "edition"
        ) in {None, "", "to_select"}:
            errors.append(f"{source}: edition_checked requires verified edition")
    if entity_type == "publication":
        errors.extend(
            _enum_error(fields, "full_text_status", FULL_TEXT_STATUSES, source)
        )
    return errors


def validate_claim_record(record: Any, source: str) -> list[str]:
    if not isinstance(record, dict):
        return _require_object(record, source)
    errors = _missing_field_errors(record, CLAIM_REQUIRED_FIELDS, source, "claim")
    errors.extend(_type_errors(record, source))
    if record.get("type") not in (None, "claim"):
        errors.append(f"{source}: invalid type '{record['type']}'")
    errors.extend(_enum_error(record, "claim_type", CLAIM_TYPES, source))
    errors.extend(_enum_error(record, "support_status", SUPPORT_STATUSES, source))
    errors.extend(_enum_error(record, "review_status", REVIEW_STATUSES, source))
    errors.extend(_review_state_errors(record, source))
    return errors


def validate_interpretation_record(record: Any, source: str) -> list[str]:
    if not isinstance(record, dict):
        return _require_object(record, source)
    errors = _missing_field_errors(
        record, INTERPRETATION_REQUIRED_FIELDS, source, "interpretation"
    )
    errors.extend(_type_errors(record, source))
    if record.get("type") not in (None, "interpretation"):
        errors.append(f"{source}: invalid type '{record['type']}'")
    errors.extend(
        _enum_error(record, "position", INTERPRETATION_POSITIONS, source)
    )
    errors.extend(_enum_error(record, "review_status", REVIEW_STATUSES, source))
    errors.extend(_review_state_errors(record, source))
    if record.get("evidence_locator") == "to_verify":
        errors.append(f"{source}: evidence_locator must be verified")
    return errors


def validate_benchmark_record(record: Any, source: str) -> list[str]:
    if not isinstance(record, dict):
        return _require_object(record, source)
    errors = _missing_field_errors(
        record, BENCHMARK_REQUIRED_FIELDS, source, "benchmark"
    )
    errors.extend(_type_errors(record, source))
    errors.extend(_enum_error(record, "difficulty", DIFFICULTIES, source))
    errors.extend(_enum_error(record, "review_status", REVIEW_STATUSES, source))
    errors.extend(_review_state_errors(record, source))
    return errors


def _record_references(record: dict[str, Any]) -> list[tuple[str, str]]:
    references: list[tuple[str, str]] = []
    for field in REFERENCE_FIELDS:
        value = record.get(field)
        if isinstance(value, str):
            references.append((field, value))
        elif isinstance(value, list):
            references.extend(
                (field, item) for item in value if isinstance(item, str)
            )
    return references


def validate_repository(root: Path) -> tuple[int, int, list[str]]:
    errors: list[str] = []
    knowledge_count = 0
    benchmark_count = 0
    entities: list[tuple[str, dict[str, Any]]] = []

    knowledge_root = root / "data" / "knowledge"
    if knowledge_root.exists():
        for path in sorted(knowledge_root.rglob("*.md")):
            if path.name == "README.md":
                continue
            source = str(path.relative_to(root))
            text = path.read_text(encoding="utf-8")
            fields = parse_frontmatter(text)
            knowledge_count += 1
            errors.extend(validate_knowledge_text(text, source))
            if fields:
                entities.append((source, fields))

        for directory, validator in (
            ("claims", validate_claim_record),
            ("interpretations", validate_interpretation_record),
        ):
            record_root = knowledge_root / directory
            if not record_root.exists():
                continue
            for path in sorted(record_root.glob("*.jsonl")):
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
                    knowledge_count += 1
                    errors.extend(validator(record, source))
                    if isinstance(record, dict):
                        entities.append((source, record))

    benchmark_records: list[tuple[str, dict[str, Any]]] = []
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
                if isinstance(record, dict):
                    benchmark_records.append((source, record))

    ids: dict[str, str] = {}
    for source, record in entities + benchmark_records:
        entity_id = record.get("id")
        if not isinstance(entity_id, str) or not entity_id:
            continue
        if entity_id in ids:
            errors.append(
                f"{source}: duplicate entity id '{entity_id}' (first seen in {ids[entity_id]})"
            )
        else:
            ids[entity_id] = source

    entity_types = {
        record["id"]: record.get("type", "benchmark")
        for _, record in entities + benchmark_records
        if isinstance(record.get("id"), str)
    }
    records_by_id = {
        record["id"]: record
        for _, record in entities
        if isinstance(record.get("id"), str)
    }

    for source, record in entities + benchmark_records:
        for field, reference in _record_references(record):
            if reference not in ids:
                errors.append(f"{source}: references missing id '{reference}'")
                continue
            allowed_types = REFERENCE_TARGET_TYPES.get(field)
            if allowed_types and entity_types.get(reference) not in allowed_types:
                expected = " or ".join(sorted(allowed_types))
                errors.append(
                    f"{source}: field '{field}' must reference type '{expected}', "
                    f"got '{entity_types.get(reference)}' for '{reference}'"
                )

        if record.get("type") == "claim" and record.get("support_status") == "source_supported":
            evidence_ids = record.get("evidence_ids")
            if not isinstance(evidence_ids, list):
                evidence_ids = []
            if any(
                records_by_id.get(evidence_id, {}).get("locator_status")
                != "passage_checked"
                for evidence_id in evidence_ids
            ):
                errors.append(
                    f"{source}: source_supported requires passage_checked evidence"
                )

        if record.get("type") == "claim":
            context = records_by_id.get(record.get("context_id"), {})
            for evidence_id in (
                record.get("evidence_ids")
                if isinstance(record.get("evidence_ids"), list)
                else []
            ):
                evidence = records_by_id.get(evidence_id, {})
                if evidence.get("work_id") != context.get("work_id"):
                    errors.append(
                        f"{source}: evidence work '{evidence.get('work_id')}' "
                        f"does not match context work '{context.get('work_id')}'"
                    )

        if record.get("type") == "interpretation":
            publication = records_by_id.get(record.get("publication_id"), {})
            if publication.get("full_text_status") != "full_text_checked":
                errors.append(
                    f"{source}: interpretation requires full_text_checked publication"
                )

        if record.get("type") == "concept_hub":
            context_ids = record.get("context_ids")
            if not isinstance(context_ids, list):
                context_ids = []
            for context_id in context_ids:
                context = records_by_id.get(context_id, {})
                if context.get("concept_id") != record.get("id"):
                    errors.append(
                        f"{source}: context backlink points to "
                        f"'{context.get('concept_id')}', expected '{record.get('id')}'"
                    )

        if record.get("type") == "contextual_sense":
            concept = records_by_id.get(record.get("concept_id"), {})
            context_ids = concept.get("context_ids")
            if isinstance(context_ids, list) and record.get("id") not in context_ids:
                errors.append(
                    f"{source}: context '{record.get('id')}' is not listed in "
                    f"concept '{record.get('concept_id')}' context_ids"
                )
            for source_id in (
                record.get("source_ids")
                if isinstance(record.get("source_ids"), list)
                else []
            ):
                source_record = records_by_id.get(source_id, {})
                if source_record.get("work_id") != record.get("work_id"):
                    errors.append(
                        f"{source}: source work '{source_record.get('work_id')}' "
                        f"does not match context work '{record.get('work_id')}'"
                    )

        review_ids = record.get("review_ids")
        if isinstance(review_ids, list):
            for review_id in review_ids:
                review_record = records_by_id.get(review_id, {})
                if review_record.get("reviewed_entity_id") != record.get("id"):
                    errors.append(
                        f"{source}: review record belongs to "
                        f"'{review_record.get('reviewed_entity_id')}', "
                        f"not '{record.get('id')}'"
                    )

    return knowledge_count, benchmark_count, errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    knowledge_count, benchmark_count, errors = validate_repository(root)

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(
        f"Validated {knowledge_count} knowledge record(s) "
        f"and {benchmark_count} benchmark item(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
