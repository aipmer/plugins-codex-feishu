# Authentication

## Required Credentials

Use a Feishu self-built app.

```bash
export FEISHU_APP_ID="cli_xxx"
export FEISHU_APP_SECRET="xxx"
```

## Recommended Auth Path

Prefer the local callback flow over manual code copy. It avoids short-lived authorization code expiry and writes tokens only to the local `.env` file.

1. Configure `FEISHU_APP_ID` and `FEISHU_APP_SECRET`.
2. Run `npm run feishu -- auth`.
3. Open the printed `AUTH_URL` in a browser and authorize the app.
4. Wait for the browser page to show `授权完成，可以回到 Codex。`.
5. Run `npm run feishu -- doctor` to verify `FEISHU_USER_ACCESS_TOKEN`.

The exchange script uses Feishu's current OAuth token endpoint `authen/v2/oauth/token`, not the legacy `authen/v1/access_token`.

## MCP Server

The plugin declares one stable local MCP server:

```bash
command -v python3
```

- `feishu-mcp`: stable local server backed by direct Feishu OpenAPI HTTP calls.

If `python3` is unavailable, install Python 3 first.

## Local Callback Auth

Export the app credentials first, or put them in `.env`:

```bash
export FEISHU_APP_ID="cli_xxx"
export FEISHU_APP_SECRET="xxx"
```

Run:

```bash
npm run feishu -- auth
```

Open the printed `AUTH_URL`. The command listens on `http://localhost:3000/callback`, exchanges the callback code immediately, then writes:

```env
FEISHU_USER_ACCESS_TOKEN=...
FEISHU_USER_REFRESH_TOKEN=...
```

Use a narrower or broader scope when needed:

```bash
npm run feishu -- auth -- --scope "offline_access wiki:wiki:readonly bitable:app"
```

Optional flags:

```bash
npm run feishu -- auth -- \
  --redirect-uri "http://localhost:3000/callback" \
  --port 3000 \
  --timeout-seconds 240
```

## Manual Code Exchange

Manual exchange is a fallback when the local callback port is unavailable.

Export the app credentials first, or put them in `.env`:

```bash
export FEISHU_APP_ID="cli_xxx"
export FEISHU_APP_SECRET="xxx"
```

Generate the authorization URL:

```bash
plugins/feishu/scripts/generate-feishu-auth-url.sh
```

Open the printed URL, authorize, then exchange the callback code:

```bash
plugins/feishu/scripts/exchange-feishu-code.sh --code "<callback_code>"
```

Optional flags:

```bash
plugins/feishu/scripts/generate-feishu-auth-url.sh \
  --scope "offline_access im:chat im:message"

plugins/feishu/scripts/exchange-feishu-code.sh \
  --code "<callback_code>" \
  --redirect-uri "http://localhost:3000/callback"
```

The script prints the raw Feishu response. On success, write the returned token to `.env` or export it for the current shell:

```bash
export FEISHU_USER_ACCESS_TOKEN="<returned_user_access_token>"
```

If the response field is `access_token`, treat it as the returned `user_access_token` from Feishu OAuth and export it as `FEISHU_USER_ACCESS_TOKEN`.
If the response includes `refresh_token`, store it locally as `FEISHU_USER_REFRESH_TOKEN`.

The stable local MCP server uses `FEISHU_USER_ACCESS_TOKEN` automatically.

## Bot Access Control

Starting with v1.1.0, the long-connection bot fails closed. Configure at least one of `FEISHU_BOT_OWNER_OPEN_ID`, `FEISHU_BOT_ADMINS`, `FEISHU_BOT_ALLOWED_USERS`, or `FEISHU_BOT_ALLOWED_CHATS`. Without one, the service can start for diagnosis but no message can trigger a local command.

## App ID vs Recipient ID

Do not confuse the app identity with the message recipient identity.

| Field | Example | Purpose | Safe to commit? |
| --- | --- | --- | --- |
| `FEISHU_APP_ID` | `cli_xxx` | Identifies your Feishu self-built app. | No real value. Use placeholders only. |
| `FEISHU_APP_SECRET` | `xxx` | App credential used to obtain tenant tokens. | Never. |
| `FEISHU_USER_ACCESS_TOKEN` | `u-xxx` | OAuth user token for user-owned resources. | Never. |
| `FEISHU_USER_REFRESH_TOKEN` | `ur-xxx` | OAuth refresh token for renewing user access. | Never. |
| `open_id` | `ou_xxxxx` | Identifies a Feishu user as a message recipient. | No real value. Use placeholders only. |
| `chat_id` | `oc_xxxxx` | Identifies a Feishu group or private chat. | No real value. Use placeholders only. |

For private assistant-style pushes, send to a user's `open_id`:

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

`FEISHU_APP_ID` answers "which app sends this message"; `open_id` answers "which user receives this message".

When a user asks to draft and send a Codex project update, verify the private push setup before sending:

1. `FEISHU_APP_ID` is configured.
2. `FEISHU_APP_SECRET` is configured.
3. A recipient `open_id` or target `chat_id` is known.
4. A short test message has been sent successfully.

If any item is missing, guide the user through setup first. Never infer an `open_id` from the app `App ID`, and never place real app IDs, secrets, tokens, `open_id`, `chat_id`, or message IDs in committed examples.

## Getting A User `open_id`

Recommended paths:

1. Ask the target user to send one private message to the bot, then inspect the Feishu event log for:

```text
event.sender.sender_id.open_id
```

2. If the app has contact permissions and the user is in the app's visibility scope, resolve by email:

```yaml
tool: mcp__feishu-mcp__contact_v3_user_batchGetId
params:
  user_id_type: open_id
data:
  emails:
    - "user@example.com"
```

Required permissions usually include:

- `contact:user.id:readonly`
- `im:message:send_as_bot`

If email lookup returns the email but no `open_id`, check app visibility scope, contact permissions, and whether the email belongs to the same Feishu tenant.

## Token Mode

- `useUAT: true`: user access token. Use this when resources should be owned by or visible to the current user.
- `useUAT: false`: tenant access token. Use this for app/bot-owned operations.

For created Docs or Bitable resources, default to `useUAT: true` unless the user explicitly wants bot-owned resources.

## Minimum Permissions

Start with narrow permissions and expand by workflow:

- Messages: `im:message:readonly`, `im:message:send_as_bot`
- Groups: `im:chat`, `im:chat.members:read`, optionally `im:chat:create`
- Docs: document read/edit permissions required by `docx` APIs
- Wiki: `wiki:wiki:readonly`, optionally `wiki:wiki`
- Drive permissions: permission member management
- Bitable: `bitable:app`
- For manual user token refresh support, add `offline_access`

Tenant admin approval may be required before production use.

## App Preconditions

Before blaming MCP runtime behavior, verify these Feishu app settings:

- The app is published and the current user can use it
- `http://localhost:3000/callback` is configured as a redirect URI
- If the app page shows a `refresh user_access_token` switch, it is enabled
- Required scopes are approved for the app and, when applicable, for user identity calls

## 中文说明

### 推荐认证路径

1. 配置 `FEISHU_APP_ID` 和 `FEISHU_APP_SECRET`。
2. 运行 `npm run feishu -- auth`。
3. 打开命令输出的 `AUTH_URL`，在浏览器完成用户授权。
4. 等浏览器显示「授权完成，可以回到 Codex。」
5. 脚本会自动换取 token，并仅写入本地 `.env` 的 `FEISHU_USER_ACCESS_TOKEN` 和 `FEISHU_USER_REFRESH_TOKEN`。

应用身份适合机器人发消息；用户身份适合搜索 Docs/Wiki、创建用户持有的 Docx 和写入用户可访问的 Bitable。`App ID` 标识发送应用，`open_id` 标识消息接收人，两者不能混用。

### Bot 访问控制

从 `v1.1.0` 开始，长连接 bot 默认拒绝执行。必须至少配置 `FEISHU_BOT_OWNER_OPEN_ID`、`FEISHU_BOT_ADMINS`、`FEISHU_BOT_ALLOWED_USERS` 或 `FEISHU_BOT_ALLOWED_CHATS` 中的一项。未配置时服务仍可启动用于诊断，但任何消息都不能触发本地命令。

### 最小权限

- 消息：`im:message:readonly`、`im:message:send_as_bot`
- 群聊：`im:chat`、`im:chat.members:read`
- Docs：读取、创建和编辑新版文档所需的 `docx` 权限
- Wiki：`wiki:wiki:readonly`
- Drive：文档元数据与链接查询所需权限
- Bitable：`bitable:app`
- 需要刷新用户 token 时增加 `offline_access`
