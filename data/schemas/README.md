# 数据字段规范

本项目把“概念”与“概念在具体文本中的语境义项”分开。Markdown frontmatter 中的数组和对象使用单行 JSON 语法，便于无第三方依赖地校验。

## 共同字段

所有知识实体必须包含：

| 字段 | 含义 |
|---|---|
| `id` | 全仓库唯一且稳定的标识 |
| `type` | 实体类型 |
| `title` | 人类可读标题 |
| `review_status` | 内容审核状态 |
| `version` | 语义版本号 |

审核状态仅允许：

```text
drafted
source_checked
philosophy_reviewed
published
```

内容是否修订应记录在 Git 历史和审核表中，不再把 `revised` 当成审核等级。

哲学内容实体从 `drafted` 晋级到 `source_checked`，以及任何实体晋级到 `philosophy_reviewed` 或 `published` 时，必须包含非空 `review_ids`，并指向确实审核该实体的 `review_record`。审核记录至少保存被审核实体、审核者别名和日期。著作、论文等纯书目元数据可在核验出版信息后直接标记 `source_checked`。

## 知识实体

### 著作 `work`

补充字段：`original_title`、`author`、`original_language`。

### 二手文献 `publication`

补充字段：`authors`、`publication_year`、`stable_identifier`、`full_text_status`。`stable_identifier` 优先保存 DOI；没有 DOI 时保存可核验的出版社、期刊或机构库链接。`full_text_status` 仅允许 `metadata_only` 或 `full_text_checked`。文献元数据通过核验，不等于其中的哲学解释已经通过审核。

### 概念入口 `concept_hub`

补充字段：

- `preferred_label`：首选中文名称；
- `original_terms`：原文术语及语言；
- `context_ids`：该概念已经建立的语境义项 ID；
- 可选 `alternative_labels`、`related_concept_ids`。

概念入口用于导航，不应制造一个跨越所有著作的唯一完整定义。
尚未建立语境义项的入口仅可在 `review_status: drafted` 时使用空数组
`context_ids: []`。一旦进入来源核验或更高审核状态，必须先建立并关联至少一个
具体语境义项，不能把候选章节或研究排期冒充为已核验语境。

### 语境义项 `contextual_sense`

补充字段：`concept_id`、`work_id`、`section`、`source_ids`。正文应说明论证位置、前置概念、适用范围和教学解释。

### 来源定位 `source_locator`

补充字段：`work_id`、`section`、`edition`、`passage_locator`、`locator_status`。定位状态仅允许：

```text
to_verify
edition_checked
passage_checked
```

不同译本页码不能混用；定位未逐项核验时必须保持 `to_verify`。
只有 `edition` 和 `passage_locator` 都已核实时，才能标记 `passage_checked`。主张只有引用 `passage_checked` 来源后才能标记 `source_supported`。

### 原子主张 `claim`

原子主张使用 JSONL，必填字段：

| 字段 | 含义 |
|---|---|
| `id` | 主张 ID |
| `type` | 固定为 `claim` |
| `text` | 单一、可核验的主张 |
| `claim_type` | 主张性质 |
| `context_id` | 所属语境义项 |
| `evidence_ids` | 支持该主张的来源定位 |
| `support_status` | 当前证据状态 |
| `review_status` | 内容审核状态 |

`claim_type` 仅允许：

```text
textual_fact
paraphrase
editorial_summary
scholarly_interpretation
pedagogical_explanation
analogy
```

`support_status` 仅允许：`to_verify`、`source_supported`、`contested`、`unsupported`。

### 解释立场 `interpretation`

解释记录使用 JSONL，必须关联已经存在的 `publication_id` 和 `claim_id`，并填写支持该立场判断的 `evidence_locator`。`position` 仅允许 `supports`、`qualifies` 或 `rejects`。只有文献标记为 `full_text_checked` 后才能创建解释记录，不能根据搜索摘要或 AI 概括直接入库。

## HegelBench-ZH

评测数据使用 JSONL，必填字段：

| 字段 | 含义 |
|---|---|
| `id` | 题目 ID |
| `category` | 题目类型 |
| `difficulty` | `beginner`、`intermediate` 或 `advanced` |
| `question` | 用户问题 |
| `related_works` | 相关著作 ID 数组 |
| `required_points` | 回答必须覆盖的要点 |
| `forbidden_errors` | 不可出现的错误 |
| `claim_ids` | 评分依据对应的主张 ID |
| `review_status` | 审核状态 |

开发集可用于调试；保留测试集不得上传到 Agent 知识库或用于提示词优化。
