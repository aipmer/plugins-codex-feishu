# Feishu for Codex

Open-source Feishu plugin for Codex, designed for high-frequency team collaboration workflows rather than as a chat substitute for Codex mobile.

[中文说明](./README.zh-CN.md)

## Maintainer

- Personal site: [pmer.cn](https://pmer.cn)
- X: [@ai_pmer](https://x.com/ai_pmer)
- Related open-source project: [Codex Blue Book](https://github.com/hunkwu/book)

## Preview

![Feishu plugin marketplace entry](./plugins/feishu/assets/screenshots/plugin-marketplace-real.png)

![Feishu plugin detail page](./plugins/feishu/assets/screenshots/plugin-detail-real.png)

![Install Feishu plugin in Codex](./plugins/feishu/assets/screenshots/plugin-install-real.png)

## What it solves

- Summarize recent messages from Feishu group chats
- Search Feishu Docs and Wiki from Codex
- Draft bot-style answers and send them back to Feishu
- Push Codex project digests into Feishu private assistant chats or group chats
- Receive Feishu event subscription webhooks for passive bot triggers and message intake
- Avoid unstable upstream beta token flows by using a local stable HTTP-backed MCP implementation

More precisely, this plugin focuses on the team collaboration layer: message-triggered execution, shared result delivery, Docs and knowledge workflows, project digests, and permission-aware organizational automation.

## 5-Minute Private Assistant Push

Use this path when you want Codex to draft a project update and push it to your Feishu private assistant chat.

```bash
git clone https://github.com/aipmer/plugins-codex-feishu.git
cd plugins-codex-feishu
cp .env.example .env
npm install
```

Edit `.env`:

```env
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx
FEISHU_DEFAULT_RECEIVE_ID=ou_xxxxx
FEISHU_DEFAULT_RECEIVE_ID_TYPE=open_id
FEISHU_DEFAULT_UPDATE_MODE=weekly
```

Verify credentials and preview the message first:

```bash
npm run feishu:doctor
npm run feishu:project-update -- --preview --mode weekly --file ./plugins/feishu/skills/feishu/examples/project-update-template.md
```

Send a short test message before sending the full update:

```bash
npm run feishu:project-update -- --test --send --confirm
npm run feishu:project-update -- --send --confirm --title "Weekly Update" --file ./digest.md
```

Useful variants:

```bash
npm run feishu:project-update -- --dry-run-json --mode daily --message "Completed: shipped docs."
npm run feishu:project-update -- --preview --receive-id ou_xxxxx --receive-id-type open_id --file ./digest.md
```

If configuration is missing, the script prints the exact missing items and setup steps. `FEISHU_APP_ID` identifies the sending app; `open_id` identifies the recipient user. Real sends require `--confirm`.

## 5-Minute Message Bot Quickstart

Use this path when you want to quickly verify Feishu message integration from this GitHub repository. It uses Feishu's official long connection mode, so you do not need a public HTTPS callback URL.

```bash
git clone https://github.com/aipmer/plugins-codex-feishu.git
cd plugins-codex-feishu
cp .env.example .env
npm install
```

Edit `.env`:

```env
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx
FEISHU_BOT_REPLY_TEXT=收到，我已接入 Codex Feishu 插件。
FEISHU_DEFAULT_WORKSPACE=/absolute/path/to/your/workspace
FEISHU_CODEX_COMMAND="node plugins/feishu/scripts/feishu-codex-runner.js"
FEISHU_CODEX_COMMAND_MODE=stdin
FEISHU_RUNNER_COMMAND="codex exec"
```

If you only want a connectivity check, `FEISHU_BOT_REPLY_TEXT` is enough. To enable the current minimal bridge flow, also set `FEISHU_CODEX_COMMAND` so incoming text messages can trigger a local command. The current command set is: `/help`, `/new`, `/status`, `/ids`, `/stop`, `/cd <path>`.

Local execution protocol:

- `FEISHU_CODEX_COMMAND_MODE=stdin`: default mode. The bot writes `Session`, `Workspace`, and the raw message text to stdin.
- `FEISHU_CODEX_COMMAND_MODE=env`: no stdin payload. Use environment variables such as `FEISHU_MESSAGE_TEXT`, `FEISHU_MESSAGE_PAYLOAD`, `FEISHU_SESSION_KEY`, `FEISHU_SESSION_WORKSPACE`, and `FEISHU_RUN_ID`.

The recommended setup is to point `FEISHU_CODEX_COMMAND` to the repo-provided runner and point `FEISHU_RUNNER_COMMAND` to the real downstream command. That keeps the bridge contract stable even when the payload shape evolves.

Minimal access control:

- `FEISHU_BOT_OWNER_OPEN_ID`: owner identity. When set, the owner can trigger execution directly.
- `FEISHU_BOT_ADMINS`: comma-separated admin `open_id` list.
- `FEISHU_BOT_ALLOWED_USERS`: comma-separated allowed user `open_id` list.
- `FEISHU_BOT_ALLOWED_CHATS`: comma-separated allowed group or chat `chat_id` list.

If all four are empty, the bot stays open. As soon as any one of them is configured, the bot switches to controlled mode and unauthorized messages receive a denial reply instead of launching a local command.

Current queue behavior:

- Each session runs at most one local task at a time.
- If a new message arrives while the current session is still running, the new message is queued instead of being dropped.
- The current version now drains multiple queued messages in order.
- `FEISHU_BOT_BATCH_WINDOW_MS` optionally enables a short batching window. When greater than `0`, messages that enter the queue within that window are combined into a single local task.

## 5-Minute Codex Bridge Check

If you want to validate the full `message -> runner -> downstream command -> reply` loop locally before calling real Codex, point the downstream command to the repo-provided echo script:

```env
FEISHU_CODEX_COMMAND="node plugins/feishu/scripts/feishu-codex-runner.js"
FEISHU_RUNNER_COMMAND="node plugins/feishu/scripts/feishu-codex-echo.js"
FEISHU_CODEX_COMMAND_MODE=env
```

This does not call Codex yet. It simply echoes the incoming message, session key, and workspace back into Feishu so you can verify the bridge contract, session isolation, and reply path first.

In Feishu Open Platform:

1. Create a self-built app and copy `App ID` / `App Secret`.
2. Go to `Events and Callbacks`.
3. Select `Receive events through long connection`.
4. Subscribe to `im.message.receive_v1`.
5. Grant `im:message` and `im:message:send_as_bot`.
6. Publish the app and add the bot to a test group.

Verify:

```bash
npm run feishu:doctor
npm run feishu:bot
```

When the terminal shows `ws client ready`, send a text message in the group such as `Please summarize today's project progress`. With the echo setup above, the bot should reply with something like:

```text
Feishu Codex Echo
Session: chat:...
Workspace: /absolute/path/to/your/workspace
Message: Please summarize today's project progress
```

After that works, switch `FEISHU_RUNNER_COMMAND` back to the real command, for example `codex exec`.

The bot stores a short recent-message history per session and ignores duplicate Feishu `message_id` deliveries, so retry delivery from Feishu does not create duplicate local executions or duplicate replies.

`/status` now includes the current `chat_id`, sender `open_id`, bridge command, runner command, and local service summary when available. `/ids` prints the current session identifiers together with allowlist-ready `FEISHU_BOT_ALLOWED_CHATS` and `FEISHU_BOT_ALLOWED_USERS` snippets.

Unified CLI entry:

- `npm run feishu -- doctor`
- `npm run feishu -- bot`
- `npm run feishu -- start`
- `npm run feishu -- stop`
- `npm run feishu -- restart`
- `npm run feishu -- status`
- `npm run feishu -- runner --print-payload`
- `npm run feishu -- push --preview --message "已完成：发布文档"`
- `npm run feishu -- webhook --self-test`

Local service management:

- This version prioritizes macOS `launchd`
- `start` generates or updates `service/launchd.plist` under the bot state directory
- `status` combines `launchctl print` output and `service/service.json` into a readable summary
- Default log paths:
  - `service/stdout.log`
  - `service/stderr.log`

Keep real credentials and Feishu identifiers in local `.env` files only. Do not commit real `FEISHU_APP_ID`, `FEISHU_APP_SECRET`, `FEISHU_USER_ACCESS_TOKEN`, `open_id`, `chat_id`, or `message_id` values in docs, examples, logs, or screenshots.

Full guide: [Quickstart Message Bot](./plugins/feishu/skills/feishu/examples/quickstart-message-bot.md)

## Core scenarios

### 1. Group message summary

Turn recent chat history into:

- decisions
- action items
- blockers
- owners

### 2. Bot conversation reply

Use Feishu chat context plus Docs or Wiki retrieval to produce concise answers for a target chat.

### 3. Codex project digest push

Generate daily or weekly project summaries from Codex and push them into Feishu chats.

### 4. Webhook event subscription

Receive Feishu Open Platform event callbacks with support for:

- `url_verification` challenge handling
- `Verification Token` source checks
- `X-Lark-Signature` checks
- `Encrypt Key` encrypted payload decryption
- stdout or local file event logs for follow-up agent workflow integration

## Repository layout

```text
.agents/plugins/marketplace.json
plugins/feishu/
```

Use `plugins/feishu` as the sparse path when importing from Git.

## Install in Codex

For regular users, the recommended path is to add this GitHub repository directly in Codex. You do not need to run `git clone` first.

In `Add Plugin Marketplace`:

- Source: `https://github.com/aipmer/plugins-codex-feishu.git`
- Git reference: `main`
- Sparse path: `plugins/feishu`

If your Codex build expects a repo-local marketplace file, use:

- Marketplace path: `.agents/plugins/marketplace.json`

After the marketplace is added, the plugin appears under `Codex Community`. That display name comes from this repository's `.agents/plugins/marketplace.json`.

### Built by OpenAI / Codex Community / Personal

- `Built by OpenAI`: official built-in plugins maintained by OpenAI.
- `Codex Community`: the community plugin marketplace added from this GitHub repository. This is the recommended path for open-source distribution.
- `Personal`: your local personal plugin directory. Use this for local development, debugging, or private plugins.

Most users only need the `Codex Community` install. You do not need to install a second copy under `Personal`. Use the developer path below only if you want to modify or contribute to the plugin.

### Developer Local Install

If you want to contribute code, debug scripts, or modify the plugin, clone the repository:

```bash
git clone https://github.com/aipmer/plugins-codex-feishu.git
cd plugins-codex-feishu
scripts/smoke-test.sh
```

If you need to sync the repository plugin into your local personal plugin runtime:

```bash
scripts/sync-local-plugin.sh
```

This syncs `plugins/feishu` one-way into the default local runtime directory. Regular install users do not need this step.

## Setup

1. Create a Feishu self-built app.
2. Add this redirect URI:

```text
http://localhost:3000/callback
```

3. Grant the scopes required by the open-source workflow:

- `im:chat`
- `im:message`
- `docx:document`
- `wiki:wiki`
- `wiki:wiki:readonly`
- `docs:document:import`
- `drive:drive`
- `contact:user.id:readonly`
- `auth:user.id:read`
- `offline_access`

4. Export credentials:

```bash
export FEISHU_APP_ID="cli_xxx"
export FEISHU_APP_SECRET="xxx"
```

5. Generate an authorization URL:

```bash
plugins/feishu/scripts/generate-feishu-auth-url.sh
```

6. After browser authorization, exchange the callback code:

```bash
plugins/feishu/scripts/exchange-feishu-code.sh --code "<callback_code>"
```

7. Export the returned token:

```bash
export FEISHU_USER_ACCESS_TOKEN="<oauth_access_token>"
```

8. Run a quick environment check:

```bash
plugins/feishu/scripts/doctor-feishu-auth.sh
```

## Webhook Server

The repository includes a minimal webhook receiver:

```bash
export FEISHU_VERIFICATION_TOKEN="xxx"
export FEISHU_ENCRYPT_KEY="xxx"

plugins/feishu/scripts/feishu_webhook_server.py
```

Default local URL:

```text
http://127.0.0.1:3000/webhook/feishu
```

Feishu Open Platform requires a public HTTPS callback URL, for example:

```text
https://your-public-domain.example/webhook/feishu
```

Configure it in your self-built app under `Events and Callbacks`, including `Encryption Strategy` and event subscriptions.

More details:

- [Webhook event subscription](./plugins/feishu/skills/feishu/reference/webhook.md)
- [Webhook to bot reply example](./plugins/feishu/skills/feishu/examples/webhook-to-reply.md)
- [Product roadmap](./docs/roadmap.md)

## Private Assistant Push

To push Codex daily reports, weekly reports, or execution summaries into a private assistant chat, use the recipient user's `open_id`, not the app's `App ID`.

The default plugin prompt prioritizes this flow:

```text
Draft a Codex project update and send it to Feishu.
```

- `FEISHU_APP_ID`: the sending Feishu self-built app, for example `cli_xxx`
- `open_id`: the recipient user, for example `ou_xxxxx`
- `chat_id`: a group or private chat, for example `oc_xxxxx`

If the private push is not configured yet, check and guide the user through:

1. Configure `FEISHU_APP_ID` and `FEISHU_APP_SECRET` in the local runtime environment.
2. Run `plugins/feishu/scripts/doctor-feishu-auth.sh` to verify app credentials and tenant token access.
3. Get the recipient user's `open_id`.
4. Send a short test message before sending the full Codex project update.
5. Set `FEISHU_DEFAULT_UPDATE_MODE` if daily or weekly is the normal default.

Recommended command path:

```bash
npm run feishu:project-update -- --preview --mode weekly --file ./plugins/feishu/skills/feishu/examples/project-update-template.md
npm run feishu:project-update -- --dry-run-json --mode daily --message "已完成：发布文档"
npm run feishu:project-update -- --test --send --confirm
npm run feishu:project-update -- --send --confirm --title "Weekly Update" --file ./digest.md
```

Recommended ways to get `open_id`:

1. Ask the target user to send one private message to the bot.
2. Inspect `event.sender.sender_id.open_id` in Feishu Open Platform event logs.
3. Or resolve the user by email when the app has `contact:user.id:readonly`.

Common failure hints:

- Missing app credentials: set `FEISHU_APP_ID` and `FEISHU_APP_SECRET`.
- Missing recipient: set `FEISHU_DEFAULT_RECEIVE_ID` or pass `--receive-id`.
- Invalid recipient type: only `open_id` and `chat_id` are supported.
- Permission failure: check `im:message`, `im:message:send_as_bot`, and tenant approval.
- Delivery failure after authorization: publish the app and verify the recipient is inside visibility scope.

More details:

- [Authentication: App ID vs Recipient ID](./plugins/feishu/skills/feishu/reference/auth.md#app-id-vs-recipient-id)
- [Messages: Send Private Assistant Message](./plugins/feishu/skills/feishu/reference/messages.md#send-private-assistant-message)

## Local Verification

After changing the plugin, run:

```bash
scripts/smoke-test.sh
```

## Community

Contributions and real-world notes are welcome:

- [Contributing guide](./CONTRIBUTING.md)
- [Case studies](./case-studies/)
- [Case study template](./case-studies/TEMPLATE.md)

Especially useful contributions include:

- Real Feishu + Codex workflow troubleshooting notes
- `AGENTS.md` rules that worked in your own project
- AI tuning tips, prompts, and verification methods
- Stories about using Codex to ship a product, get users, or earn first revenue

## Stable runtime

The default `feishu-mcp` entry in `.mcp.json` uses the local HTTP-backed implementation in:

- `plugins/feishu/scripts/feishu_http_mcp.py`

The upstream beta server is not included in the default plugin runtime. The stable local HTTP-backed server is the recommended path.

## Official workflow examples

- [Group message summary](./plugins/feishu/skills/feishu/examples/group-summary.md)
- [Bot conversation reply](./plugins/feishu/skills/feishu/examples/bot-reply.md)
- [Codex project digest push](./plugins/feishu/skills/feishu/examples/project-digest-push.md)

## Notes

- Tokens are expected to stay in environment variables by default and are not written into repo files.
- The stable local MCP directly wraps the high-frequency IM, Docs, Wiki, and Contacts flows.
- Less common endpoints can still be reached through `feishu_openapi_request`.
- The repository is intended to be importable directly from GitHub as a Codex plugin marketplace source.

## Related Project

- [hunkwu/book](https://github.com/hunkwu/book) - Codex Blue Book, focused on Codex workflows, multi-surface orchestration, and AI-native product delivery.
