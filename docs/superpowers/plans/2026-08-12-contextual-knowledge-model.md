# Contextual Knowledge Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a machine-checkable contextual knowledge sample for Hegel's concept of recognition and separate content revision scoring from Agent blind evaluation.

**Architecture:** Keep human-readable concept and context cards in Markdown with JSON-compatible frontmatter values. Store atomic claims and future interpretation records as JSONL, connect all entities with stable IDs, and extend the existing dependency-free Python validator to check schemas, enums, unique IDs, and references.

**Tech Stack:** Markdown, JSONL, Python standard library, `unittest`, GitHub pull requests.

## Global Constraints

- All new philosophical content remains `drafted` until a recorded expert review exists.
- No full modern Chinese translations or copyrighted article bodies enter the repository.
- Do not create interpretation records from abstracts or search snippets alone.
- Automated validation checks structure, not philosophical truth.

---

### Task 1: Define executable schema expectations

**Files:**
- Modify: `tests/test_validate_data.py`
- Modify: `data/schemas/README.md`

**Interfaces:**
- Consumes: existing `validate_repository(root)` entry point.
- Produces: test fixtures for contextual Markdown entities and JSONL claims.

- [x] Add failing tests for typed frontmatter values, claim enums, duplicate IDs, and broken references.
- [x] Run `python -m unittest discover -s tests -v` and confirm failures are caused by missing validation behavior.
- [x] Document the five entity types and controlled vocabularies.

### Task 2: Extend the validator

**Files:**
- Modify: `scripts/validate_data.py`
- Test: `tests/test_validate_data.py`

**Interfaces:**
- Produces: `parse_frontmatter(text) -> dict[str, Any]`, JSONL entity validation, and repository reference validation.

- [x] Parse JSON-compatible frontmatter arrays and scalar values without adding dependencies.
- [x] Validate required fields and controlled enum values by entity type.
- [x] Detect duplicate IDs and references to missing entities.
- [x] Run the full unit test suite until all tests pass.

### Task 3: Build the recognition sample

**Files:**
- Create: `data/knowledge/concepts/recognition.md`
- Create: `data/knowledge/contexts/recognition-phenomenology-self-consciousness.md`
- Create: `data/knowledge/sources/phenomenology-self-consciousness.md`
- Create: `data/knowledge/claims/recognition.jsonl`
- Create: `data/knowledge/interpretations/README.md`
- Create: `data/benchmark/development.jsonl`

**Interfaces:**
- Consumes: entity IDs and vocabularies from `data/schemas/README.md`.
- Produces: the first connected concept-context-source-claim-benchmark slice.

- [x] Migrate the existing recognition draft into a concept hub and a contextual sense card.
- [x] Extract atomic claims and bind each to the contextual sense and source locator.
- [x] Keep source locations that still need edition checking marked `to_verify`.
- [x] Keep philosophical content and benchmark records marked `drafted`; the bibliographic work record is `source_checked`.

### Task 4: Separate review workflows

**Files:**
- Modify: `eval/review-form.md`
- Modify: `eval/rubric.md`
- Modify: `CONTRIBUTING.md`
- Modify: `README.md`

**Interfaces:**
- Produces: a two-pass content review form and a blind Agent evaluation procedure.

- [x] Add initial diagnostic score, revision log, final acceptance score, and hard failure checks.
- [x] State that Agent answers are scored before human correction.
- [x] Explain contextual senses and interpretation records to contributors.

### Task 5: Verify and publish

**Files:**
- Review all files in this branch.

**Interfaces:**
- Produces: a pushed feature branch and a draft pull request against `main`.

- [x] Run `python -m unittest discover -s tests -v`.
- [x] Run `python scripts/validate_data.py`.
- [x] Inspect `git diff --check`, repository status, and the complete diff.
- [ ] Commit only intended files, push `agent/contextual-knowledge-model`, and open a draft PR.
