# Feishu for Codex

面向 Codex 的开源飞书插件，重点服务于高频团队协作场景。

[English README](./README.md)

## 维护者

- 个人站点：[pmer.cn](https://pmer.cn)
- X 账号：[@ai_pmer](https://x.com/ai_pmer)
- 关联开源项目：[Codex 蓝皮书](https://github.com/hunkwu/book)

## 预览

![Feishu 插件市场入口](./plugins/feishu/assets/screenshots/plugin-marketplace-real.png)

![Feishu 插件详情页](./plugins/feishu/assets/screenshots/plugin-detail-real.png)

![在 Codex 中安装 Feishu 插件](./plugins/feishu/assets/screenshots/plugin-install-real.png)

## 解决什么问题

- 总结飞书群聊最近消息
- 在 Codex 里搜索飞书文档和知识库
- 生成机器人式回复并回推到飞书
- 将 Codex 项目日报、周报推送到飞书群
- 接收飞书事件订阅 Webhook，用于机器人被动触发和群消息入口
- 用本地稳定 HTTP MCP 实现，绕开上游 beta token 链路不稳定的问题

## 核心场景

### 1. 飞书群消息总结

把最近群消息整理成：

- 决策事项
- 待办事项
- 风险阻塞
- 责任人

### 2. 机器人式对话回复

结合飞书聊天上下文，以及 Docs / Wiki 检索结果，生成面向群聊或私聊的简洁回复。

### 3. Codex 项目总结推送

基于 Codex 项目进展自动生成日报或周报，并推送到飞书群。

### 4. Webhook 事件订阅

接收飞书开放平台事件订阅回调，支持：

- `url_verification` challenge 校验
- `Verification Token` 来源校验
- `X-Lark-Signature` 签名校验
- `Encrypt Key` 加密事件体解密
- 将事件输出到 stdout 或本地日志文件，便于后续接入 agent workflow

## 仓库结构

```text
.agents/plugins/marketplace.json
plugins/feishu/
```

通过 Git 导入时，稀疏路径使用 `plugins/feishu`。

## 在 Codex 中安装

普通用户推荐直接在 Codex 里通过 GitHub 仓库添加插件市场，不需要先手动执行 `git clone`。

在 `Add Plugin Marketplace` 中填写：

- Source：`https://github.com/hunkwu/plugins-codex-feishu.git`
- Git reference：`main`
- Sparse path：`plugins/feishu`

如果当前 Codex 版本需要 repo-local marketplace 文件，则使用：

- Marketplace path：`.agents/plugins/marketplace.json`

添加成功后，插件会出现在 `Codex Community` 这个市场下。这个名称来自仓库内的 `.agents/plugins/marketplace.json`。

### Built by OpenAI / Codex Community / Personal 的区别

- `Built by OpenAI`：Codex 官方内置插件，通常由 OpenAI 维护。
- `Codex Community`：从这个 GitHub 仓库添加的社区插件市场，适合开源分发和普通用户安装。
- `Personal`：用户本机个人插件目录，适合自己本地开发、调试或未公开插件。

一般用户只需要安装 `Codex Community` 这一份，不需要再安装到 `Personal`。如果你要参与开发或修改插件源码，再使用下面的开发者方式。

### 开发者本地安装

如果你要贡献代码、调试脚本或修改插件，可以先克隆仓库：

```bash
git clone https://github.com/hunkwu/plugins-codex-feishu.git
cd plugins-codex-feishu
scripts/smoke-test.sh
```

如果需要把仓库内插件同步到本机个人插件目录：

```bash
scripts/sync-local-plugin.sh
```

这会把 `plugins/feishu` 单向同步到默认的本地运行时目录。普通安装用户不需要执行这一步。

## 配置步骤

1. 创建飞书自建应用。
2. 配置回调地址：

```text
http://localhost:3000/callback
```

3. 为开源版默认工作流开通这些权限：

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

4. 导出应用凭据：

```bash
export FEISHU_APP_ID="cli_xxx"
export FEISHU_APP_SECRET="xxx"
```

5. 生成授权链接：

```bash
plugins/feishu/scripts/generate-feishu-auth-url.sh
```

6. 浏览器授权后，用回调里的 `code` 换 token：

```bash
plugins/feishu/scripts/exchange-feishu-code.sh --code "<callback_code>"
```

7. 导出返回的 token：

```bash
export FEISHU_USER_ACCESS_TOKEN="<oauth_access_token>"
```

8. 运行环境检查：

```bash
plugins/feishu/scripts/doctor-feishu-auth.sh
```

## Webhook 服务

本仓库内置轻量 Webhook 接收服务：

```bash
export FEISHU_VERIFICATION_TOKEN="xxx"
export FEISHU_ENCRYPT_KEY="xxx"

plugins/feishu/scripts/feishu_webhook_server.py
```

默认监听：

```text
http://127.0.0.1:3000/webhook/feishu
```

飞书开放平台配置时需要使用公网 HTTPS 地址，例如：

```text
https://your-public-domain.example/webhook/feishu
```

配置位置：飞书开放平台自建应用 -> `事件与回调` -> `加密策略` 和 `事件订阅`。

详细指引见：

- [Webhook 事件订阅](./plugins/feishu/skills/feishu/reference/webhook.md)
- [Webhook 到机器人回复示例](./plugins/feishu/skills/feishu/examples/webhook-to-reply.md)

## 私人助理推送

如果希望把 Codex 日报、周报或执行总结推送到个人私聊，需要使用接收人的 `open_id`，不是应用的 `App ID`。

- `FEISHU_APP_ID`：发送消息的飞书自建应用，例如 `cli_xxx`
- `open_id`：接收消息的用户，例如 `ou_xxxxx`
- `chat_id`：群聊或私聊会话，例如 `oc_xxxxx`

获取 `open_id` 的推荐方式：

1. 让目标用户先给机器人发一条私聊消息。
2. 在飞书开放平台事件日志里查看 `event.sender.sender_id.open_id`。
3. 或在具备 `contact:user.id:readonly` 权限时，用邮箱解析用户 ID。

详细说明见：

- [Authentication: App ID vs Recipient ID](./plugins/feishu/skills/feishu/reference/auth.md#app-id-vs-recipient-id)
- [Messages: Send Private Assistant Message](./plugins/feishu/skills/feishu/reference/messages.md#send-private-assistant-message)

## 本地验证

修改插件后建议运行：

```bash
scripts/smoke-test.sh
```

## 社区共建

欢迎提交真实使用经验和改进：

- [贡献指南](./CONTRIBUTING.md)
- [实战案例库](./case-studies/)
- [案例模板](./case-studies/TEMPLATE.md)

优先欢迎这些内容：

- Codex + 飞书 workflow 的真实踩坑和修复
- 你项目中有效的 `AGENTS.md` 规则
- AI 调优技巧、提示词和验证方法
- 独立开发者如何用 Codex 快速上线产品、拿到用户或赚到第一笔收入

## 稳定运行时

默认 `feishu-mcp` 入口使用本地稳定 HTTP 实现，核心脚本位于：

- `plugins/feishu/scripts/feishu_http_mcp.py`

默认插件运行时不再包含上游 beta server。推荐使用当前稳定的本地 HTTP 封装服务。

## 官方 workflow 示例

- [飞书群消息总结](./plugins/feishu/skills/feishu/examples/group-summary.md)
- [机器人式对话回复](./plugins/feishu/skills/feishu/examples/bot-reply.md)
- [Codex 项目总结推送](./plugins/feishu/skills/feishu/examples/project-digest-push.md)

## 说明

- 默认不把 token 写入仓库文件，建议只放在环境变量里。
- 稳定本地 MCP 已直接封装高频的 IM、Docs、Wiki、Contacts 能力。
- 更少用或更专门的接口仍然可以通过 `feishu_openapi_request` 调用。
- 这个仓库的目标是让用户可以直接用 GitHub 仓库地址导入 Codex 插件市场。

## 关联项目

- [hunkwu/book](https://github.com/hunkwu/book) - Codex 蓝皮书，聚焦 Codex 工作流、多端编排和 AI 原生产品落地。
