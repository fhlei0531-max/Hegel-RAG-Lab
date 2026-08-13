# Concept Hub Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reviewable core catalog of Hegel concept-hub drafts without inventing source evidence or overwriting hand-edited cards.

**Architecture:** Store catalog metadata as UTF-8 JSON, render missing Markdown concept hubs with a dependency-free Python script, and test both catalog integrity and no-overwrite behavior. Keep contextual senses and evidence records out of this batch.

**Tech Stack:** Python standard library, JSON, Markdown frontmatter, `unittest`

## Global Constraints

- Every generated card uses `review_status: drafted`.
- No generated quotation, page number, passage locator, or secondary-literature conclusion.
- Existing files, especially `recognition.md`, are never overwritten.
- Candidate contexts are planning hints, not verified source locators.

---

### Task 1: Catalog contract and generator

**Files:**
- Create: `data/catalogs/hegel-core-concepts.json`
- Create: `scripts/generate_concept_hubs.py`
- Create: `tests/test_generate_concept_hubs.py`

- [ ] Write tests for required catalog fields, unique IDs, valid related IDs, rendering, check mode, and no-overwrite behavior.
- [ ] Run the focused tests and confirm they fail because the generator does not exist.
- [ ] Implement the dependency-free generator and catalog loader.
- [ ] Run the focused tests and confirm they pass.

### Task 2: Generated cards and review index

**Files:**
- Create: `data/knowledge/concepts/*.md`
- Create: `docs/concept-catalog.md`
- Modify: `README.md`

- [ ] Generate all missing concept-hub drafts from the catalog.
- [ ] Add a review index grouped by major textual domain.
- [ ] Document the batch boundary and the workflow for deepening one card.
- [ ] Run full tests, repository validation, generator check mode, and `git diff --check`.

### Task 3: Publish review branch

- [ ] Inspect the diff for accidental source claims or generated review promotions.
- [ ] Commit the batch as one reviewable feature.
- [ ] Push `agent/concept-hub-catalog` to GitHub.
