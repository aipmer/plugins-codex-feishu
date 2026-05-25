# Long-Connection Message Bot Quickstart

## English

### Summary

This maintainer case study records the quick verification path for Feishu message integration. A local long-connection bot receives `im.message.receive_v1` and replies to group text messages without requiring a public HTTPS callback URL.

### Workflow

- Create a Feishu self-built app.
- Enable long connection event delivery.
- Subscribe to `im.message.receive_v1`.
- Grant `im:message` and `im:message:send_as_bot`.
- Run `npm run feishu:doctor`.
- Run `npm run feishu:bot`.

### What Worked

- Long connection is faster than webhook setup for local verification.
- The bot reply proves both event intake and message sending.
- The workflow gives contributors a repeatable smoke path before adding Codex-specific logic.

### What To Improve

- Support private chat events, not only group text messages.
- Add optional Codex-generated replies after the static reply path is stable.

## 中文

### 摘要

这是飞书消息集成的快速验证案例。本地长连接机器人接收 `im.message.receive_v1`，并回复群文本消息，不需要公网 HTTPS 回调地址。

### 流程

- 创建飞书自建应用。
- 开启长连接事件订阅。
- 订阅 `im.message.receive_v1`。
- 开通 `im:message` 和 `im:message:send_as_bot`。
- 运行 `npm run feishu:doctor`。
- 运行 `npm run feishu:bot`。

### 有效做法

- 本地验证阶段，长连接比 webhook 配置更快。
- 机器人回复同时验证了事件接收和消息发送。
- 这个流程能让贡献者在加入 Codex 逻辑前先跑通基础链路。

### 后续改进

- 支持私聊事件，不只支持群文本消息。
- 静态回复稳定后，再接入 Codex 生成回复。
