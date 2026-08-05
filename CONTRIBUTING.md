# 贡献指南

感谢你帮助改进 Hegel-RAG-Lab。本项目优先接受能够提高哲学准确性、文本可追溯性和教学价值的贡献。

## 数据生命周期

```text
drafted
→ source_checked
→ philosophy_reviewed
→ published
→ revised
```

- `drafted`：初稿，尚未核对来源。
- `source_checked`：已定位相关著作和章节。
- `philosophy_reviewed`：经过哲学专业评审者审核。
- `published`：通过格式检查和项目审核，可进入正式知识库。
- `revised`：发布后根据评测或反馈进行过修订。

初次提交请使用 `drafted` 或 `source_checked`。除非确有评审记录，不要自行标记为 `philosophy_reviewed`。

## 提交流程

1. 从真实学习问题出发建立 Issue。
2. 使用对应模板编写概念卡、章节导读或误解纠正。
3. 标明一手文本位置；二手解释需注明性质和来源。
4. 运行自动化测试与数据验证器。
5. 请求哲学内容审核。
6. 在 Pull Request 中说明修改原因和已知边界。

## 内容要求

- 一张知识卡集中解决一个主要问题。
- 明确区分直接引语、转述和教学性概括。
- 不编造黑格尔原文、章节、页码或参考文献。
- 不将“正反合”等入门简化当作充分解释。
- 对存在争议的问题标明解释范围。
- 通俗例子不能改变概念的核心含义。

## 版权与隐私

- 不提交仍受版权保护的现代中文译本全文或扫描件。
- 必要短引须标明来源和译本。
- 评审者可使用别名；未经同意不要公开真实姓名和私人反馈。
- 不提交 API Key、访问令牌或 `.env` 文件。

## Commit 建议

```text
data: add recognition concept card
benchmark: add self-consciousness questions
docs: clarify philosophy review workflow
fix: correct ethical life explanation
```
