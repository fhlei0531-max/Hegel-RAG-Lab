# 数据字段规范

## 知识卡

知识卡使用 Markdown，文件顶部必须包含由 `---` 包围的 frontmatter。

必填字段：

| 字段 | 含义 | 示例 |
|---|---|---|
| `id` | 全仓库唯一标识 | `concept-recognition-001` |
| `type` | 数据类型 | `concept` |
| `title` | 中文标题 | `承认` |
| `works` | 相关著作，使用逗号分隔 | `精神现象学` |
| `review_status` | 审核状态 | `drafted` |
| `version` | 数据版本 | `0.1.0` |

示例：

```markdown
---
id: concept-recognition-001
type: concept
title: 承认
works: 精神现象学
review_status: drafted
version: 0.1.0
---
```

允许的数据类型：

```text
source_locator
concept
chapter_guide
misconception
relationship
```

允许的审核状态：

```text
drafted
source_checked
philosophy_reviewed
published
revised
```

## HegelBench-ZH 题目

评测数据使用 JSONL，一行一个 JSON 对象。必填字段：

| 字段 | 类型 | 含义 |
|---|---|---|
| `id` | string | 唯一题目编号 |
| `category` | string | 题目类型 |
| `difficulty` | string | `beginner`、`intermediate` 或 `advanced` |
| `question` | string | 用户问题 |
| `related_works` | array | 相关著作 |
| `required_points` | array | 高质量答案必须覆盖的要点 |
| `forbidden_errors` | array | 不可出现的错误 |
| `source_ids` | array | 对应知识卡 ID |
| `review_status` | string | 审核状态 |

开发集可用于反复调试；保留测试集不能上传到 Agent 知识库。
