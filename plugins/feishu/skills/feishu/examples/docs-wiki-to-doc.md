# Docs/Wiki Retrieval To Doc Write-Back

Use case: search Feishu Docs or Wiki, summarize context with Codex, then write the result back to a new Feishu Doc.

## Suggested flow

1. Search Docs or Wiki by keyword.
2. Read the most relevant document content.
3. Ask Codex to summarize background, decisions, risks, and next steps.
4. Create a new Docx document and append structured content blocks.
5. Send the created document link or token back to the target chat.

Recommended single path:

1. Search Docs first when the user already knows the document topic.
2. Search Wiki when the knowledge is likely organized in a space hierarchy.
3. Resolve the final Docx token before summarizing.
4. Write back as a new Doc with `useUAT: true` when the current user should open it directly.

## Summary Template

Use this structure for the generated write-back content:

```md
# Project Context Summary

## Background

-

## Key Points

-

## Risks

-

## Suggested Next Actions

-
```

## Search Docs

```yaml
tool: mcp__feishu-mcp__docx_builtin_search
data:
  search_key: "project launch checklist"
  count: 10
useUAT: true
```

## Search Wiki

```yaml
tool: mcp__feishu-mcp__wiki_v1_node_search
data:
  query: "project launch checklist"
  page_size: 10
useUAT: true
```

## Read Content

```yaml
tool: mcp__feishu-mcp__docx_v1_document_rawContent
path:
  document_id: "doxcnxxxxxx"
useUAT: true
```

## Write Back To Feishu Docs

```yaml
tool: mcp__feishu-mcp__docx_v1_document_create
data:
  title: "Codex Project Context"
useUAT: true
```

Append the generated sections with `docx_v1_documentBlockChildren_create`, then resolve the document URL with `drive_v1_meta_batchQuery`.

## Minimum Permissions

- Search Docs: `docx:document`
- Search Wiki: `wiki:wiki:readonly`
- Create and edit Docs: `docx:document`
- Resolve document URL: `drive:drive`
- Drive access may be required by the tenant or target location: `drive:drive`

Permission guidance:

- Docs search and raw-content read workflows can stay read-only.
- Wiki search and Wiki node lookup can stay read-only.
- Write-back requires user-identity `docx:document` permission.
- Use `useUAT: true` when the created document should be owned by or visible to the current user.

## Failure Paths

- No search result: refine the keyword or search the other surface, Docs vs Wiki.
- Wiki result cannot map to a Docx object: inspect the resolved node type before calling Docx APIs.
- Read works but creation fails: the authorized user likely lacks Docx creation or edit permission.
- Write-back succeeds but the user cannot open the doc: confirm `useUAT: true`, target visibility, and Drive permissions.

## 中文说明

### 用途

这个示例适合「从飞书知识中找资料，再把 Codex 的总结写回飞书文档」的场景。

### 推荐流程

1. 先按关键词搜索 Docs 或 Wiki
2. 读取最相关的文档内容
3. 让 Codex 总结背景、关键点、风险和下一步
4. 创建新版 Docx，并把总结转换为结构化块写入
5. 把新文档链接或 token 发回目标聊天

单一路径建议：

1. 用户已经知道主题时，优先先搜 Docs
2. 知识更像空间目录时，再搜 Wiki
3. 总结前先拿到最终 Docx token
4. 如果文档需要当前用户直接打开，写回时用 `useUAT: true`

### 摘要模板

推荐生成的文档结构：

```md
# Project Context Summary

## Background

-

## Key Points

-

## Risks

-

## Suggested Next Actions

-
```

### 最小权限

- `docx:document`：搜索和读取 Docs
- `wiki:wiki:readonly`：搜索和读取 Wiki
- `docx:document`：创建和编辑新版文档
- `drive:drive`：查询最终文档链接
- `drive:drive`：部分租户或目标位置需要

权限边界：

- Docs 搜索和 Docx 读取可以保持只读
- Wiki 搜索和节点解析也可以保持只读
- 写回动作需要用户身份具备 `docx:document`
- 如果文档需要当前用户直接持有或打开，使用 `useUAT: true`

### 失败路径

- 搜不到结果：换关键词，或在 Docs / Wiki 之间切换
- Wiki 无法映射到 Docx：先确认节点实际对象类型
- 能读不能写：检查当前用户是否具备新版文档创建和编辑权限
- 写回成功但用户打不开：检查 `useUAT: true`、可见范围和 Drive 权限
