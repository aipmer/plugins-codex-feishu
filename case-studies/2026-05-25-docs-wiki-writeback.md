# Docs/Wiki Retrieval And Write-Back

## English

### Summary

This maintainer case study describes the target Docs/Wiki workflow for v0.2: Codex searches Feishu knowledge, summarizes the relevant context, writes a new Feishu Doc, and sends the resulting reference back to the chat.

### Workflow

- Search Feishu Docs by keyword.
- Search Wiki nodes when the context is organized in Wiki.
- Read the selected document raw content.
- Ask Codex to produce a concise project background or decision summary.
- Import the final Markdown into Feishu Docs.
- Send the result back through Feishu IM.

### What Worked

- Keeping search, read, summarize, and write-back as separate steps makes permission failures easier to diagnose.
- User token mode is the safer default when the created document should be directly opened by the current user.

### What To Improve

- Add stronger examples for choosing the right document among search results.
- Add a final message template that includes document title, summary, and link.

## 中文

### 摘要

这是 v0.2 的 Docs/Wiki 目标 workflow 案例：Codex 搜索飞书知识，整理相关上下文，写入新的飞书文档，再把结果引用发回聊天。

### 流程

- 按关键词搜索飞书 Docs。
- 如果知识沉淀在 Wiki 中，则搜索 Wiki 节点。
- 读取选中文档的原始内容。
- 让 Codex 生成项目背景或决策摘要。
- 将最终 Markdown 导入飞书 Docs。
- 通过飞书 IM 发回结果。

### 有效做法

- 把搜索、读取、总结和写回拆开，权限失败时更容易定位。
- 如果创建的文档需要当前用户直接打开，默认使用 user token mode 更合适。

### 后续改进

- 增加如何从搜索结果中选择正确文档的示例。
- 增加最终消息模板，包含文档标题、摘要和链接。
