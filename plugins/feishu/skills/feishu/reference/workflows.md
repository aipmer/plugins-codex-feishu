# Workflows

## Summarize Recent Group Messages

1. Use `im_v1_chat_list` to find the target chat.
2. Use `im_v1_message_list` to fetch recent messages.
3. Summarize decisions, blockers, owners, and next actions.
4. Optionally send the summary back through `im_v1_message_create`.

## Bot-Style Feishu Reply

1. Use `wiki_v1_node_search` with the user's topic.
2. Resolve promising nodes with `wiki_v2_space_getNode`.
3. Read Docx content when the node points to a document.
4. Draft a concise answer for the user or group.
5. Send the reply with `im_v1_message_create`.

## Codex Project Digest Push

1. Collect the relevant Codex project progress inputs.
2. Structure the content into `Completed`, `In Progress`, `Risks`, and `Next Steps`.
3. Preview the rendered message locally before sending.
4. Send a short test message to the configured `open_id` or `chat_id`.
5. Send the digest to the target chat with `im_v1_message_create`.

Local command path:

```bash
npm run feishu:project-update -- --preview --mode weekly --file ./plugins/feishu/skills/feishu/examples/project-update-template.md
npm run feishu:project-update -- --dry-run-json --mode daily --message "Completed: shipped docs."
npm run feishu:project-update -- --test --send --confirm
npm run feishu:project-update -- --send --confirm --title "Codex 周报" --file ./plugins/feishu/skills/feishu/examples/project-update-template.md
```

If the command reports missing configuration, guide the user through `FEISHU_APP_ID`, `FEISHU_APP_SECRET`, `FEISHU_DEFAULT_RECEIVE_ID`, `FEISHU_DEFAULT_RECEIVE_ID_TYPE`, and optionally `FEISHU_DEFAULT_UPDATE_MODE` before sending.

## Docs/Wiki Retrieval To Doc Write-Back

Recommended path:

1. Search Feishu Docs by keyword.
2. If no good result appears, search Wiki with the same keyword.
3. Resolve the final document token and read the selected Docx content.
4. Summarize into `Background`, `Key Points`, `Risks`, and `Suggested Next Actions`.
5. Import the final Markdown into Feishu Docs with `useUAT: true` if the current user should open it directly.
6. Send the created document reference back to the target chat.

Failure path guidance:

- No document found: refine the search key or switch from Docs to Wiki.
- Wiki result does not resolve to Docx: inspect the node object type first.
- Read works but import fails: check `docs:document:import`.
- Import succeeds but the user cannot open the doc: verify user visibility and Drive permissions.

See `examples/docs-wiki-to-doc.md`.

## Write Automation Result to Bitable

1. Locate `app_token` and `table_id`.
2. Use `feishu_openapi_request` to query or update the relevant Bitable endpoint.
3. Create or update the record.
4. Push a concise completion message to Feishu IM.

Recommended initial tables:

- Project status
- Release records
- Risk tracker
- Case study intake

See `examples/bitable-project-templates.md`.

## Event Subscription Extension

For bot mentions or passive message intake, use the bundled webhook receiver or deploy the same flow to your own service:

```text
Feishu event callback
  -> verify challenge
  -> verify token
  -> decrypt event when Encrypt Key is enabled
  -> normalize event
  -> call agent workflow
  -> send result with im_v1_message_create
```

Local receiver:

```bash
export FEISHU_VERIFICATION_TOKEN="xxx"
export FEISHU_ENCRYPT_KEY="xxx"

scripts/feishu_webhook_server.py
```

Cloudflare Workers, Vercel Functions, or an existing OpenClaw/Hermes service are suitable production hosts.

See `reference/webhook.md` for the Feishu Open Platform configuration checklist.

## 中文说明

### 最近群消息总结

推荐流程：

1. 用 `im_v1_chat_list` 找到目标群聊
2. 用 `im_v1_message_list` 读取最近消息
3. 整理成决策、阻塞、责任人和下一步动作
4. 需要时再通过 `im_v1_message_create` 回推总结结果

### 机器人式飞书回复

推荐先搜索 Wiki，再解析节点，再读取对应 Docx 内容，最后生成简洁回复并发回群聊或私聊。这样比直接拼消息上下文更稳定。

### Codex 项目进展推送

推荐流程：

1. 收集项目进展输入
2. 统一整理成 `Completed`、`In Progress`、`Risks`、`Next Steps`
3. 本地预览消息
4. 先发一条短测试消息
5. 再发送正式更新

推荐命令：

```bash
npm run feishu:project-update -- --preview --mode weekly --file ./plugins/feishu/skills/feishu/examples/project-update-template.md
npm run feishu:project-update -- --dry-run-json --mode daily --message "Completed: shipped docs."
npm run feishu:project-update -- --test --send --confirm
npm run feishu:project-update -- --send --confirm --title "Codex 周报" --file ./plugins/feishu/skills/feishu/examples/project-update-template.md
```

如果命令提示缺少配置，优先检查：

- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `FEISHU_DEFAULT_RECEIVE_ID`
- `FEISHU_DEFAULT_RECEIVE_ID_TYPE`
- `FEISHU_DEFAULT_UPDATE_MODE`

### Docs / Wiki 检索并写回文档

单一路径建议：

1. 先搜索 Docs
2. 没有合适结果时，再搜索 Wiki
3. 解析最终文档 token，并读取 Docx 内容
4. 总结成 `Background`、`Key Points`、`Risks`、`Suggested Next Actions`
5. 用 `useUAT: true` 导入新文档
6. 把文档引用再发回飞书消息

失败路径建议：

- 搜不到文档：换关键词，或从 Docs 切到 Wiki
- Wiki 结果无法映射到 Docx：先检查节点对象类型
- 能读不能写：检查 `docs:document:import`
- 写回成功但用户打不开：检查可见范围和 Drive 权限

### 将结果写入多维表格

当前推荐表：

- Project status
- Release records
- Risk tracker
- Case study intake

如果当前 MCP 还没有你要用的稳定 Bitable wrapper，先走 `feishu_openapi_request`。当前阶段重点是交付接入范式，不是完整抽象层。

### 事件订阅扩展

Webhook 生产链路建议保持固定顺序：

```text
飞书事件回调
  -> challenge 校验
  -> token 校验
  -> Encrypt Key 解密
  -> 事件归一化
  -> 调用 agent workflow
  -> 用 im_v1_message_create 回推结果
```
