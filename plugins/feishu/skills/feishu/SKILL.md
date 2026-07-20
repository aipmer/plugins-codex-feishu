---
name: feishu
description: Use when working with Feishu IM, Docs, Wiki, Bitable, groups, permissions, chat history, or message push workflows through MCP-backed OpenAPI tools.
---

# Feishu

Use this skill when the user asks to operate Feishu, Feishu Docs, Wiki, groups, chat history, bot-style replies, or Feishu push workflows from Codex.

## Operating Rules

1. Prefer the `mcp__feishu-mcp__...` tool namespace when available. The hyphen matters.
2. Do not invent tokens, IDs, chat IDs, document IDs, or app credentials.
3. Use `useUAT: true` when creating resources the current user must directly access.
4. Use `useUAT: false` for application or tenant identity operations when user ownership is not needed.
5. Treat IM history as permission-scoped. Only read messages visible to the app, bot, or authorized user.
6. For message APIs, `content` must be a JSON string, not an object.
7. Prefer `open_id` for user IDs unless a workflow explicitly requires another ID type.

## Common Tool Families

- Messages: `im_v1_message_create`, `im_v1_message_list`
- Groups: `im_v1_chat_list`, `im_v1_chatMembers_get`
- Docs: `docx_builtin_search`, `docx_v1_document_rawContent`
- Docs write-back: `docx_v1_document_create`, `docx_v1_documentBlockChildren_create`, `drive_v1_meta_batchQuery`
- Wiki: `wiki_v1_node_search`, `wiki_v2_space_getNode`
- Contacts: `contact_v3_user_batchGetId`
- Generic fallback: `feishu_openapi_request`
- Bitable record write: `bitable_v1_appTableRecord_create`
- Webhook receiver: `scripts/feishu_webhook_server.py`
- Private assistant push script: `scripts/feishu-project-update.js`

The stable local MCP server currently wraps the core IM, Docs, Wiki, and Contacts flows directly. For Bitable, permissions, and other less-common endpoints, use `feishu_openapi_request` until a dedicated stable wrapper is added.

## Quick Examples

Send a text message to a group:

```yaml
tool: mcp__feishu-mcp__im_v1_message_create
params:
  receive_id_type: chat_id
data:
  receive_id: "oc_xxxxx"
  msg_type: "text"
  content: "{\"text\":\"Codex task finished.\"}"
```

Read recent chat history:

```yaml
tool: mcp__feishu-mcp__im_v1_message_list
path:
  container_id_type: chat
  container_id: "oc_xxxxx"
params:
  page_size: 20
```

Search Docs:

```yaml
tool: mcp__feishu-mcp__docx_builtin_search
data:
  search_key: "增长日报"
  count: 10
useUAT: true
```

Read a document:

```yaml
tool: mcp__feishu-mcp__docx_v1_document_rawContent
path:
  document_id: "doxcnxxxxxx"
useUAT: true
```

Search Wiki:

```yaml
tool: mcp__feishu-mcp__wiki_v1_node_search
data:
  query: "产品方案"
  page_size: 10
useUAT: true
```

## Official Workflows

- Group summary: summarize recent group messages into decisions, action items, blockers, and owners.
- Bot reply: search Docs or Wiki, compose an answer, and push it back to a target Feishu chat.
- Codex project digest push: summarize project progress and push an update into a Feishu chat on a schedule.
- Feishu-native project report: collect Git progress, retrieve Docs/Wiki context, generate a structured report, write a Docx document, and optionally append a Bitable record before message delivery.
- Private assistant push: preview a Codex project update, send a short test message, then send the final update to a user's `open_id`.
- Docs/Wiki write-back: search knowledge, summarize with Codex, and import the result into a Feishu Doc.
- Bitable project operations: sync project status, risks, release records, and case study intake into Feishu Base/Bitable.
- Webhook to bot reply: receive `im.message.receive_v1`, draft a reply with Codex, and send it back to the same chat.

## References

- Authentication and setup: `reference/auth.md`
- Messages and chat history: `reference/messages.md`
- Documents: `reference/documents.md`
- Wiki and knowledge base: `reference/wiki.md`
- Bitable: `reference/bitable.md`
- Permissions: `reference/permissions.md`
- Webhook event subscription: `reference/webhook.md`
- Reusable workflows: `reference/workflows.md`
- Project update push example: `examples/project-digest-push.md`
- Docs/Wiki write-back example: `examples/docs-wiki-to-doc.md`
- Bitable project templates: `examples/bitable-project-templates.md`

## Boundaries

The plugin packages Codex-side guidance and MCP server configuration. It does not bypass Feishu tenant admin approval, app permission review, bot visibility rules, external user limits, or message retention limits.
