# Private Assistant Push For Codex Project Updates

## English

### Summary

This maintainer case study records the first Feishu private assistant workflow for Feishu for Codex: Codex drafts a project update, previews it locally, sends a short test message, then pushes the final update to a Feishu private assistant chat.

### Workflow

- Configure a Feishu self-built app with `FEISHU_APP_ID` and `FEISHU_APP_SECRET`.
- Get the recipient user's `open_id`.
- Preview the outgoing update with `npm run feishu:project-update -- --preview`.
- Send a short test message with `npm run feishu:project-update -- --test --send`.
- Send the final update with `npm run feishu:project-update -- --send --file ./digest.md`.

### What Worked

- A private assistant chat is easier to validate than a new test group.
- Sending a test message before the full digest catches most configuration mistakes.
- The most important distinction is `FEISHU_APP_ID` for the app and `open_id` for the recipient.

### What To Improve

- Add richer card messages after the plain-text workflow is stable.
- Add a saved recipient profile for repeat sends.

## 中文

### 摘要

这是 Feishu for Codex 的维护者案例，记录第一条飞书私人助理推送 workflow：Codex 生成项目更新，本地预览，先发短测试消息，再把最终更新推送到飞书私人助理私聊。

### 流程

- 使用 `FEISHU_APP_ID` 和 `FEISHU_APP_SECRET` 配置飞书自建应用。
- 获取接收人的 `open_id`。
- 用 `npm run feishu:project-update -- --preview` 预览消息。
- 用 `npm run feishu:project-update -- --test --send` 发送短测试消息。
- 用 `npm run feishu:project-update -- --send --file ./digest.md` 发送最终更新。

### 有效做法

- 私人助理私聊比新建测试群更容易验证。
- 正式发送前先发测试消息，可以提前暴露大多数配置问题。
- 最容易混淆的是 `FEISHU_APP_ID` 和 `open_id`：前者是应用身份，后者是接收人身份。

### 后续改进

- 纯文本流程稳定后，再增加富文本卡片消息。
- 增加可复用的默认接收人配置。
