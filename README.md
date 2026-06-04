# Feishu for Codex

Open-source Feishu plugin for Codex.
Chinese-first documentation with a short English summary.
Focus: message-triggered local execution, Docs and Wiki retrieval, private assistant push, and lightweight team collaboration automation.

面向 Codex 的开源飞书插件，重点服务于高频团队协作场景：飞书消息触发、本地执行、结果回写、文档检索与项目播报。

<img src="./plugins/feishu/assets/screenshots/plugin-detail-real.png" alt="Feishu 插件预览" width="720">

## 这是什么

它不是把 Codex 简单搬到另一个聊天窗口，而是把飞书变成一个「团队协作入口」：

- 飞书群或私聊消息触发本地执行
- 通过 MCP 检索 Docs / Wiki，并把结果发送回飞书
- 将已整理的 Codex 项目日报、周报推送到飞书
- 在 macOS 上通过 `launchd` 常驻运行
- 访问控制、队列、状态反馈和最小命令体系

## 亮点

- **消息桥接**：`message -> runner -> downstream command -> reply`
- **本地稳定运行**：默认使用本地 HTTP-backed `feishu-mcp`
- **最小 bot 能力已可用**：`/help`、`/new`、`/status`、`/ids`、`/stop`、`/cd <path>`
- **轻量日报入口**：`digest --preview` / `digest --send --confirm`
- **维护边界清晰**：优先小而稳，不把仓库做成重型调度系统

## 先看哪条路径

如果你第一次接入，建议按目标直接选：

1. **只想把项目更新推送到飞书私聊**
   - 看「[5 分钟私人助理推送](#5-分钟私人助理推送)」
2. **想让飞书消息触发本地 Codex 执行**
   - 看「[5 分钟消息机器人快速接入](#5-分钟消息机器人快速接入)」
3. **想先验证 bridge，不直接调用真实 Codex**
   - 看「[5 分钟 Codex Bridge 验证](#5-分钟-codex-bridge-验证)」

## 5 分钟私人助理推送

适合场景：Codex 生成项目更新，然后推送到你的飞书私人助理私聊。

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
FEISHU_DEFAULT_RECEIVE_ID=ou_xxxxx
FEISHU_DEFAULT_RECEIVE_ID_TYPE=open_id
FEISHU_DEFAULT_UPDATE_MODE=weekly
```

先验证并预览：

```bash
npm run feishu:doctor
npm run feishu:project-update -- --preview --mode weekly --file ./plugins/feishu/skills/feishu/examples/project-update-template.md
```

真实发送：

```bash
npm run feishu:project-update -- --test --send --confirm
npm run feishu:project-update -- --send --confirm --title "Codex 周报" --file ./plugins/feishu/skills/feishu/examples/project-update-template.md
```

更轻的日报入口：

```bash
npm run feishu -- digest --preview
npm run feishu -- digest --send --confirm
```

说明：

- `FEISHU_APP_ID` 是发送消息的应用身份
- `open_id` 是接收消息的用户身份
- 真实发送必须带 `--confirm`

## 5 分钟消息机器人快速接入

适合场景：让飞书消息进入本地 bot，再触发本地命令执行。

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
FEISHU_DEFAULT_WORKSPACE=/absolute/path/to/your/workspace
FEISHU_CODEX_COMMAND="node plugins/feishu/scripts/feishu-codex-runner.js"
FEISHU_CODEX_COMMAND_MODE=stdin
FEISHU_RUNNER_COMMAND="codex exec"
```

如果只想先测连通性，只配 `FEISHU_BOT_REPLY_TEXT` 即可。
如果要启用当前版本的最小 bridge，额外配置 `FEISHU_CODEX_COMMAND` 和 `FEISHU_RUNNER_COMMAND`。

在飞书开放平台中：

1. 创建企业自建应用，复制 `App ID` / `App Secret`
2. 在「事件与回调」中选择「使用长连接接收事件」
3. 订阅 `im.message.receive_v1`
4. 开通 `im:message` 和 `im:message:send_as_bot`
5. 发布应用，并把机器人加入测试群

本地启动：

```bash
npm run feishu:doctor
npm run feishu:bot
```

如果后续要改为后台常驻：

```bash
npm run feishu -- start
npm run feishu -- status
```

## 5 分钟 Codex Bridge 验证

如果你想先验证「消息 -> runner -> 下游命令 -> 回复文本」，先不要直接调用真实 Codex，改成仓库自带 echo：

```env
FEISHU_CODEX_COMMAND="node plugins/feishu/scripts/feishu-codex-runner.js"
FEISHU_RUNNER_COMMAND="node plugins/feishu/scripts/feishu-codex-echo.js"
FEISHU_CODEX_COMMAND_MODE=env
```

这样机器人会把收到的消息、会话和工作区信息原样回给飞书，适合先验证：

- bridge 协议
- 会话隔离
- 回复链路

验证通过后，再把 `FEISHU_RUNNER_COMMAND` 切回真实命令，例如 `codex exec`。

## 核心命令

统一 CLI：

```bash
npm run feishu -- doctor
npm run feishu -- digest --preview
npm run feishu -- bot
npm run feishu -- start
npm run feishu -- stop
npm run feishu -- restart
npm run feishu -- status
npm run feishu -- runner --print-payload
npm run feishu -- push --preview --message "已完成：发布文档"
npm run feishu -- webhook --self-test
```

飞书聊天中的最小命令集：

- `/help`
- `/new`
- `/status`
- `/ids`
- `/stop`
- `/cd <path>`

## 核心能力

### 1. 飞书群消息总结

把最近群消息整理成：

- 决策事项
- 待办事项
- 风险阻塞
- 责任人

### 2. 机器人式对话回复

在具备权限时，可结合最近消息、Docs / Wiki 检索结果，生成面向群聊或私聊的简洁回复。

### 3. Codex 项目总结推送

将已整理的 Codex 项目进展按模板生成日报或周报，并推送到飞书私人助理或群聊。

### 4. Webhook 事件订阅

接收飞书开放平台事件订阅回调，支持：

- `url_verification` challenge 校验
- `Verification Token` 来源校验
- `X-Lark-Signature` 签名校验
- `Encrypt Key` 加密事件体解密
- 将事件输出到 stdout 或本地日志文件

## 访问控制与运行说明

最小访问控制：

- `FEISHU_BOT_OWNER_OPEN_ID`
- `FEISHU_BOT_ADMINS`
- `FEISHU_BOT_ALLOWED_USERS`
- `FEISHU_BOT_ALLOWED_CHATS`

如果这四项都不配，bot 默认开放；只要配置了任意一项，就会进入受控模式。

当前队列行为：

- 同一会话只会串行执行一个本地任务
- 新消息到达时如果当前会话仍在执行，会先进入队列
- 已支持多条排队消息按顺序自动 drain
- `FEISHU_BOT_BATCH_WINDOW_MS` 可选开启短窗口批处理

本地 service 管理：

- 当前 service 管理优先支持 macOS `launchd`
- `start` 会生成或更新 `service/launchd.plist`
- `status` 会结合 `launchctl print` 和 `service/service.json` 输出摘要

如果你只想在自己机器上做一个最小定时任务，当前推荐直接在 macOS `launchd` 里调用：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.hunkwu.feishu-codex.digest</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/zsh</string>
    <string>-lc</string>
    <string>cd /path/to/plugins-codex-feishu && npm run feishu -- digest --send --confirm</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Hour</key>
    <integer>21</integer>
    <key>Minute</key>
    <integer>0</integer>
  </dict>
</dict>
</plist>
```

当前仓库只提供这类文档级接入方式，不内建第二套 schedule service 管理。

## 安装到 Codex

普通用户推荐直接在 Codex 里通过 GitHub 仓库添加插件市场，不需要先手动执行 `git clone`。

在 `Add Plugin Marketplace` 中填写：

- Source：`https://github.com/aipmer/plugins-codex-feishu.git`
- Git reference：`main`
- Sparse path：`plugins/feishu`

如果当前 Codex 版本需要 repo-local marketplace 文件，则使用：

- Marketplace path：`.agents/plugins/marketplace.json`

开发者本地同步：

```bash
./scripts/sync-local-plugin.sh
```

## 稳定运行时

默认 `feishu-mcp` 入口使用本地稳定 HTTP 实现：

- `plugins/feishu/scripts/feishu_http_mcp.py`

默认插件运行时不再包含上游 beta server。推荐使用当前稳定的本地 HTTP 封装服务。

## 本地验证

修改插件后建议运行：

```bash
scripts/smoke-test.sh
```

## 延伸阅读

- [贡献指南](./CONTRIBUTING.md)
- [CHANGELOG](./CHANGELOG.md)
- [开发任务记录](./docs/dev_task.md)
- [飞书群消息总结](./plugins/feishu/skills/feishu/examples/group-summary.md)
- [机器人式对话回复](./plugins/feishu/skills/feishu/examples/bot-reply.md)
- [Codex 项目总结推送](./plugins/feishu/skills/feishu/examples/project-digest-push.md)
- [aipmer/book](https://github.com/aipmer/book)

## 说明

- 默认不把 token 写入仓库文件，建议只放在环境变量里
- 更少用或更专门的接口仍然可以通过 `feishu_openapi_request` 调用
- 真实凭证和飞书标识只保留在本地 `.env`
- 不要把真实 `FEISHU_APP_ID`、`FEISHU_APP_SECRET`、`FEISHU_USER_ACCESS_TOKEN`、`open_id`、`chat_id` 或 `message_id` 写进文档、示例、日志或截图
