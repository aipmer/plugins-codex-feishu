# Feishu for Codex

面向 Codex 的开源飞书插件，重点服务于高频团队协作场景。

[English README](./README.md)

## 预览

![Feishu for Codex 仓库概览](./plugins/feishu/assets/screenshots/github-repo-overview.png)

![在 Codex 中导入](./plugins/feishu/assets/screenshots/codex-import-marketplace.png)

## 解决什么问题

- 总结飞书群聊最近消息
- 在 Codex 里搜索飞书文档和知识库
- 生成机器人式回复并回推到飞书
- 将 Codex 项目日报、周报推送到飞书群
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

## 仓库结构

```text
.agents/plugins/marketplace.json
plugins/feishu/
```

通过 Git 导入时，稀疏路径使用 `plugins/feishu`。

## 在 Codex 中安装

在 `Add Plugin Marketplace` 中填写：

- Source：`https://github.com/hunkwu/plugins-codex-feishu.git`
- Git reference：`main`
- Sparse path：`plugins/feishu`

如果当前 Codex 版本需要 repo-local marketplace 文件，则使用：

- Marketplace path：`.agents/plugins/marketplace.json`

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

## 稳定运行时

默认 `lark-mcp` 入口使用本地稳定 HTTP 实现，核心脚本位于：

- `plugins/feishu/scripts/feishu_http_mcp.py`

上游官方 beta server 仍然保留为 `lark-mcp-official-beta`，仅用于对比调试，不建议作为生产主路径。

## 官方 workflow 示例

- [飞书群消息总结](./plugins/feishu/skills/feishu/examples/group-summary.md)
- [机器人式对话回复](./plugins/feishu/skills/feishu/examples/bot-reply.md)
- [Codex 项目总结推送](./plugins/feishu/skills/feishu/examples/project-digest-push.md)

## 说明

- 默认不把 token 写入仓库文件，建议只放在环境变量里。
- 稳定本地 MCP 已直接封装高频的 IM、Docs、Wiki、Contacts 能力。
- 更少用或更专门的接口仍然可以通过 `feishu_openapi_request` 调用。
- 这个仓库的目标是让用户可以直接用 GitHub 仓库地址导入 Codex 插件市场。
