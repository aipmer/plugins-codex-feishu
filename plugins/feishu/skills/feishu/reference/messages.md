# Messages

## Send Text

```yaml
tool: mcp__feishu-mcp__im_v1_message_create
params:
  receive_id_type: chat_id
data:
  receive_id: "oc_xxxxx"
  msg_type: "text"
  content: "{\"text\":\"Hello from Codex.\"}"
```

`content` must be a JSON string.

## Send Private Assistant Message

Use `open_id` for private assistant-style pushes to one user.

```yaml
tool: mcp__feishu-mcp__im_v1_message_create
params:
  receive_id_type: open_id
data:
  receive_id: "ou_xxxxx"
  msg_type: "text"
  content: "{\"text\":\"Codex project digest is ready.\"}"
useUAT: false
```

`open_id` is the recipient user ID. It is different from `FEISHU_APP_ID`, which identifies the sending app.

Ways to get `open_id`:

- Ask the user to send the bot a private message, then read `event.sender.sender_id.open_id` from Feishu event logs.
- Use `contact_v3_user_batchGetId` with email, if the app has `contact:user.id:readonly` and the user is in app visibility scope.

Do not commit real `open_id`, `chat_id`, `App ID`, app secret, or access token values. Use placeholders such as `ou_xxxxx`, `oc_xxxxx`, and `cli_xxx` in docs.

## Project Update Command Path

Recommended local command flow:

```bash
npm run feishu:project-update -- --preview --mode weekly --file ./plugins/feishu/skills/feishu/examples/project-update-template.md
npm run feishu:project-update -- --dry-run-json --mode daily --message "Completed: shipped docs."
npm run feishu:project-update -- --test --send --confirm
npm run feishu:project-update -- --send --confirm --title "Codex 周报" --file ./plugins/feishu/skills/feishu/examples/project-update-template.md
```

Environment defaults:

- `FEISHU_DEFAULT_RECEIVE_ID`
- `FEISHU_DEFAULT_RECEIVE_ID_TYPE`
- `FEISHU_DEFAULT_UPDATE_MODE`

The command renders this standard structure for non-test updates:

- `Completed`
- `In Progress`
- `Risks`
- `Next Steps`

## Troubleshooting

- `Missing FEISHU_APP_ID`: set the sending app ID in `.env` or the shell environment.
- `Missing FEISHU_APP_SECRET`: set the sending app secret in `.env` or the shell environment.
- `Missing FEISHU_DEFAULT_RECEIVE_ID or --receive-id`: configure the recipient user `open_id` or target `chat_id`.
- `Invalid receive_id_type`: only `open_id` and `chat_id` are supported.
- `Real sends require --confirm`: the command stays in preview mode until `--confirm` is provided.
- `Feishu rejected the request due to missing permissions`: check `im:message`, `im:message:send_as_bot`, and tenant approval.
- `The bot may not be published, or the recipient is outside app visibility`: publish the app and verify the target user is within visibility scope.

## Read Chat History

```yaml
tool: mcp__feishu-mcp__im_v1_message_list
path:
  container_id_type: chat
  container_id: "oc_xxxxx"
params:
  page_size: 20
```

Reading history requires message read permissions and is limited to the app or user authorization scope.

## List Chats

```yaml
tool: mcp__feishu-mcp__im_v1_chat_list
params:
  page_size: 50
```

## Get Chat Members

```yaml
tool: mcp__feishu-mcp__im_v1_chatMembers_get
path:
  chat_id: "oc_xxxxx"
params:
  member_id_type: open_id
```

## Create Group

The stable local MCP server does not yet provide a dedicated `im_v1_chat_create` wrapper. Use `feishu_openapi_request` if you need this endpoint before a first-class wrapper is added.

## 中文说明

### 发送文本消息

使用 `im_v1_message_create` 向群聊或目标会话发送文本消息时，`content` 必须是 JSON 字符串，不能直接传对象。

### 发送私人助理消息

私人助理场景优先使用 `open_id` 作为接收人 ID。
`open_id` 是接收人身份，`FEISHU_APP_ID` 是发送消息的应用身份，两者不能混用。

获取 `open_id` 的常见方式：

- 让目标用户先给机器人发一条私聊消息，再从事件日志读取 `event.sender.sender_id.open_id`
- 如果应用具备 `contact:user.id:readonly`，可用邮箱通过 `contact_v3_user_batchGetId` 解析

文档和示例里不要提交真实的 `open_id`、`chat_id`、`App ID`、secret 或 access token，统一使用 `ou_xxxxx`、`oc_xxxxx`、`cli_xxx` 这类占位值。

### 项目更新命令路径

推荐的本地命令流程：

```bash
npm run feishu:project-update -- --preview --mode weekly --file ./plugins/feishu/skills/feishu/examples/project-update-template.md
npm run feishu:project-update -- --dry-run-json --mode daily --message "Completed: shipped docs."
npm run feishu:project-update -- --test --send --confirm
npm run feishu:project-update -- --send --confirm --title "Codex 周报" --file ./plugins/feishu/skills/feishu/examples/project-update-template.md
```

环境变量默认值：

- `FEISHU_DEFAULT_RECEIVE_ID`
- `FEISHU_DEFAULT_RECEIVE_ID_TYPE`
- `FEISHU_DEFAULT_UPDATE_MODE`

非测试消息会被统一整理成这 4 个段落：

- `Completed`
- `In Progress`
- `Risks`
- `Next Steps`

### 常见报错

- `Missing FEISHU_APP_ID`：发送应用 ID 没有配置
- `Missing FEISHU_APP_SECRET`：发送应用 secret 没有配置
- `Missing FEISHU_DEFAULT_RECEIVE_ID or --receive-id`：没有配置接收人 `open_id` 或目标 `chat_id`
- `Invalid receive_id_type`：当前只支持 `open_id` 和 `chat_id`
- `Real sends require --confirm`：没有显式确认，命令会停留在预览模式
- `Feishu rejected the request due to missing permissions`：通常是 `im:message`、`im:message:send_as_bot` 或租户审批缺失
- `The bot may not be published, or the recipient is outside app visibility`：通常是应用未发布，或目标用户不在应用可见范围内

### 读取聊天记录与群成员

读取聊天记录依赖消息读取权限，并且只能读取应用或用户授权范围内可见的内容。
如果需要创建群聊，当前稳定 MCP 还没有专门的 `im_v1_chat_create` wrapper，可以先走 `feishu_openapi_request`。
