# Changelog

所有重要变更统一记录在这里。

## [1.0.0] - 2026-06-04

### Added

- 飞书长连接 bot bridge：`message -> runner -> downstream command -> reply`。
- 统一 CLI 入口：`npm run feishu -- <command>`。
- 仓库内置 runner 和 echo 验证路径，方便先验证 bridge，再接真实 `codex exec`。
- 最小聊天命令集：
  - `/help`
  - `/new`
  - `/status`
  - `/ids`
  - `/stop`
  - `/cd <path>`
- 访问控制：
  - owner
  - admins
  - allowed users
  - allowed chats
- 串行队列、短窗口批处理、重复消息幂等保护。
- macOS 优先的 `launchd` service 管理：
  - `start`
  - `stop`
  - `restart`
  - `status`
- 轻量日报入口：
  - `npm run feishu -- digest --preview`
  - `npm run feishu -- digest --send --confirm`
- 稳定 HTTP-backed `feishu-mcp`，覆盖 IM、Docs、Wiki、Contacts 以及通用 OpenAPI 请求。

### Changed

- README 调整为中文优先，突出亮点、快速接入路径和真实功能边界。
- CONTRIBUTING 调整为中文优先，并保留英文说明，方便中文用户先读、国际用户快速理解贡献方式。
- `package.json`、插件清单、MCP / Webhook 可见版本统一到 `1.0.0` 口径。
- 默认 digest 文案和模板改为中文，更适合飞书私人助理推送场景。
- 项目文档结构收口为：
  - `README.md`
  - `CHANGELOG.md`
  - `docs/roadmap.md`
  - `docs/pre-release-checklist.md`
  - `docs/dev_task.md`
- 定时日报不作为内建 schedule 子系统，只提供轻量脚本和仓库外 `launchd` 示例。

### Fixed

- 修正真实联调中错误 Feishu `App ID` 导致的消息无法进入本地 bot 问题。
- 增加基于 `message_id` 的重复投递保护，避免飞书重试导致重复执行和重复回复。
- 收口本地联调说明，减少 bot 运行状态、`launchd` service 状态和真实推送状态之间的混淆。

### Verification

- `bash scripts/smoke-test.sh`
- `scripts/check-sensitive-values.sh`
- `npm run feishu -- help`
- `npm run feishu -- digest --preview`
- `npm run feishu -- webhook --self-test`
- 真实飞书 bot bridge 回复链路验证通过
- 真实私人助理推送与轻量 digest 发送验证通过
