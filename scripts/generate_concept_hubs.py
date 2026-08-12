from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / "data" / "catalogs" / "hegel-core-concepts.json"
DEFAULT_OUTPUT = ROOT / "data" / "knowledge" / "concepts"


def load_catalog(path: Path) -> list[dict[str, Any]]:
    document = json.loads(path.read_text(encoding="utf-8"))
    concepts = document.get("concepts")
    if not isinstance(concepts, list):
        raise ValueError("catalog field 'concepts' must be a list")
    return concepts


def render_card(entry: dict[str, Any]) -> str:
    frontmatter = [
        "---",
        f"id: {entry['id']}",
        "type: concept_hub",
        f"title: {entry['preferred_label']}",
        f"preferred_label: {entry['preferred_label']}",
        "original_terms: "
        + json.dumps(entry["original_terms"], ensure_ascii=False, separators=(",", ":")),
        "alternative_labels: "
        + json.dumps(entry.get("alternative_labels", []), ensure_ascii=False),
        "context_ids: []",
        "related_concept_ids: "
        + json.dumps(entry.get("related_concept_ids", []), ensure_ascii=False),
        "review_status: drafted",
        "version: 0.1.0",
        "---",
        "",
        f"# {entry['preferred_label']}",
        "",
        "> 状态：AI 辅助生成的术语导航初稿，尚未完成一手文本定位与哲学专业审核。",
        "",
        "## 导航说明",
        "",
        f"本卡是“{entry['preferred_label']}”的概念入口，不提供跨越黑格尔全部著作的单一定义。"
        "具体含义、论证功能和适用边界，应在后续语境义项中绑定到著作、章节和来源定位后分别说明。",
        "",
        "## 原文术语与译名",
        "",
    ]

    for term in entry["original_terms"]:
        frontmatter.append(f"- `{term['value']}`（{term['language']}）")
    aliases = entry.get("alternative_labels", [])
    if aliases:
        frontmatter.append(f"- 常见或候选译名：{'、'.join(aliases)}")
    else:
        frontmatter.append("- 暂无已登记别名；仍需检查不同中译本的译名差异。")

    frontmatter.extend(["", "## 候选语境（待核验）", ""])
    for candidate in entry["candidate_contexts"]:
        frontmatter.append(f"- {candidate}")

    frontmatter.extend(
        [
            "",
            "以上条目只用于安排后续研究，不等于已核实的章节定位或文本结论。",
            "",
            "## 待核验问题",
            "",
        ]
    )
    for question in entry["verification_questions"]:
        frontmatter.append(f"- {question}")

    frontmatter.extend(
        [
            "",
            "## 后续加工清单",
            "",
            "- [ ] 核对德文词形、中文首选译名和异译；",
            "- [ ] 选定首个具体著作与论证段落；",
            "- [ ] 创建来源定位卡并核验版本；",
            "- [ ] 创建语境义项，说明论证位置、前置概念和适用边界；",
            "- [ ] 拆分可核验的原子主张；",
            "- [ ] 记录二手研究的不同解释立场；",
            "- [ ] 由哲学专业审核者诊断、修订并验收。",
            "",
        ]
    )
    return "\n".join(frontmatter)


def generate(concepts: list[dict[str, Any]], output: Path) -> tuple[int, int]:
    output.mkdir(parents=True, exist_ok=True)
    created = 0
    skipped = 0
    for entry in concepts:
        path = output / entry["filename"]
        if path.exists():
            skipped += 1
            continue
        path.write_text(render_card(entry), encoding="utf-8")
        created += 1
    return created, skipped


def inspect_cards(
    concepts: list[dict[str, Any]], output: Path
) -> tuple[list[str], list[str], list[str]]:
    missing: list[str] = []
    mismatched: list[str] = []
    drifted: list[str] = []
    for entry in concepts:
        path = output / entry["filename"]
        if not path.exists():
            missing.append(entry["filename"])
            continue
        actual = path.read_text(encoding="utf-8")
        expected_line = f"id: {entry['id']}"
        if expected_line not in actual.splitlines():
            mismatched.append(entry["filename"])
            continue
        if entry["id"] == "concept-recognition":
            continue
        if actual != render_card(entry):
            drifted.append(entry["filename"])
    return missing, mismatched, drifted


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate missing Hegel concept hubs")
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    concepts = load_catalog(args.catalog)
    if args.check:
        missing, mismatched, drifted = inspect_cards(concepts, args.output)
        if missing:
            print(f"Missing {len(missing)} concept card(s): {', '.join(missing)}")
        if mismatched:
            print(
                f"Mismatched {len(mismatched)} concept card ID(s): "
                + ", ".join(mismatched)
            )
        if drifted:
            print(
                f"Drifted {len(drifted)} generated concept card(s): "
                + ", ".join(drifted)
            )
        if missing or mismatched or drifted:
            return 1
        print(f"All {len(concepts)} catalog concept card(s) exist.")
        return 0

    created, skipped = generate(concepts, args.output)
    print(f"Created {created} concept card(s); skipped {skipped} existing card(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
