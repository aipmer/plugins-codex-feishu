# Quickstart Message Bot

Use this flow when a GitHub user wants to quickly verify Feishu message integration without a public callback URL.

## Goal

Run a local long-connection Feishu bot that replies to group text messages:

```text
收到，我已接入 Codex Feishu 插件。
```

## 1. Clone And Install

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

## 中文说明

### 用途

这个 quickstart 适合快速验证飞书消息链路，不需要公网回调地址。
它使用飞书官方长连接模式，本地就可以接收事件并回复群消息。

### 目标

跑起一个本地长连接 Feishu bot，对群文本消息自动回复：

```text
收到，我已接入 Codex Feishu 插件。
```

### 1. 克隆并安装

```bash
git clone https://github.com/aipmer/plugins-codex-feishu.git
cd plugins-codex-feishu
cp .env.example .env
npm install
```

编辑 `.env`：

```env
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx
FEISHU_BOT_REPLY_TEXT=收到，我已接入 Codex Feishu 插件。
```

`.env` 只保留在本地，不要提交真实应用凭证。

### 2. 配置飞书应用

在飞书开放平台里：

1. 创建自建应用
2. 把 `App ID` 和 `App Secret` 填入 `.env`
3. 进入 `Events and Callbacks`
4. 选择：

```text
Receive events through long connection
```

5. 订阅：

```text
im.message.receive_v1
```

6. 开通权限：

```text
im:message
im:message:send_as_bot
```

7. 发布应用
8. 把机器人加入测试群

这个 quickstart 不需要 `FEISHU_VERIFICATION_TOKEN`、`FEISHU_ENCRYPT_KEY`，也不需要公网 HTTPS 回调地址。

### 3. 验证

先检查应用凭证：

```bash
npm run feishu:doctor
```

再启动 bot：

```bash
npm run feishu:bot
```

终端出现：

```text
ws client ready
```

说明长连接已建立。
此时在测试群里发一条普通文本消息，终端应输出类似：

```json
{"event_type":"im.message.receive_v1","chat_id":"oc_xxx","source_message_id":"om_xxx","reply_message_id":"om_xxx"}
```

群里应收到自动回复：

```text
收到，我已接入 Codex Feishu 插件。
```

### 常见问题

- `ws client ready` 但没有回复：通常是订阅完 `im.message.receive_v1` 后还没发布应用
- 收不到事件：确认机器人已经在测试群里，且发送的是普通文本消息
- 回复时报权限错误：检查 `im:message:send_as_bot`
- 凭证错误：重新执行 `npm run feishu:doctor`，确认 `FEISHU_APP_ID` 和 `FEISHU_APP_SECRET`

这个 quickstart 刻意保持简单，目标是先把消息链路跑通，再继续接入 Codex 工作流、Docs/Wiki 检索或项目总结推送。
