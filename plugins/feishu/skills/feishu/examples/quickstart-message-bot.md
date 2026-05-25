# Quickstart Message Bot

Use this flow when a GitHub user wants to quickly verify Feishu message integration without a public callback URL.

## Goal

Run a local long-connection Feishu bot that replies to group text messages:

```text
收到，我已接入 Codex Feishu 插件。
```

## 1. Clone And Install

```bash
git clone https://github.com/hunkwu/plugins-codex-feishu.git
cd plugins-codex-feishu
cp .env.example .env
npm install
```

Edit `.env`:

```env
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx
FEISHU_BOT_REPLY_TEXT=收到，我已接入 Codex Feishu 插件。
```

Keep `.env` local. Do not commit real app credentials.

## 2. Configure Feishu App

In Feishu Open Platform:

1. Create a self-built app.
2. Copy `App ID` and `App Secret` into `.env`.
3. Go to `Events and Callbacks`.
4. Choose:

```text
Receive events through long connection
```

5. Subscribe to:

```text
im.message.receive_v1
```

6. Grant permissions:

```text
im:message
im:message:send_as_bot
```

7. Publish the app.
8. Add the bot to a test group.

You do not need `FEISHU_VERIFICATION_TOKEN`, `FEISHU_ENCRYPT_KEY`, or a public HTTPS callback URL for this quickstart.

## 3. Verify

Check app credentials:

```bash
npm run feishu:doctor
```

Start the bot:

```bash
npm run feishu:bot
```

Expected startup evidence:

```text
ws client ready
```

Send a normal text message in the test group. Expected terminal output:

```json
{"event_type":"im.message.receive_v1","chat_id":"oc_xxx","source_message_id":"om_xxx","reply_message_id":"om_xxx"}
```

Expected group reply:

```text
收到，我已接入 Codex Feishu 插件。
```

## Troubleshooting

- `ws client ready` but no reply: publish the app after subscribing to `im.message.receive_v1`, then retry.
- No event received: make sure the bot is in the test group and the message is normal text.
- Permission error when replying: check `im:message:send_as_bot`.
- Credential error: rerun `npm run feishu:doctor` and verify `FEISHU_APP_ID` / `FEISHU_APP_SECRET`.

The quickstart bot is intentionally simple. Use it to verify message integration first, then extend it with Codex workflows, Docs/Wiki retrieval, or project digest pushes.
