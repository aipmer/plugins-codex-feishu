# Changelog

所有重要变更统一记录在这里。

## [0.3.2] - 2026-06-04

### Added

- 轻量日报入口：
  - `npm run feishu -- digest --preview`
  - `npm run feishu -- digest --send --confirm`
- 仓库内置 digest 包装脚本，复用现有 Feishu 项目更新发送链路。
- `/ids` 命令，用于快速获取当前 `chat_id`、`open_id` 和 allowlist 配置片段。
- 更丰富的 `/status` 输出，补充 bridge command、runner command 和本地 service 摘要。

### Changed

- 默认日报、周报推送改为更偏向中文输出。
- 默认 digest 模板已经完整中文化，适合真实私人助理推送场景。
- 文档改为推荐仓库外 macOS `launchd` 示例，不再扩展为第二套内建调度子系统。

### Fixed

- 修正了一次真实联调里使用错误 Feishu `App ID` 导致的消息无法进入本地 bot 问题。
- 增加基于 `message_id` 的重复投递保护，避免重复执行和重复回复。
- 收口本地联调说明，减少 bot 运行状态、`launchd` service 状态和真实推送状态之间的混淆。

### Verification

- `bash scripts/smoke-test.sh`
- `scripts/check-sensitive-values.sh`
- `npm run feishu -- digest --preview`
- `npm run feishu -- digest --send --confirm`
- 真实飞书 bot bridge 回复链路验证通过

## [0.3.0-beta] - 2026-06-04

### Added

- 统一 CLI 入口：`npm run feishu -- <command>`
- Feishu bot bridge：`message -> runner -> downstream command -> reply`
- 仓库内置 runner 和 echo 本地验证路径
- 最小命令集：`/help`、`/new`、`/status`、`/stop`、`/cd <path>`
- 访问控制：
  - owner
  - admins
  - allowed users
  - allowed chats
- 串行队列、短窗口批处理、重复消息幂等保护
- macOS 优先的 `launchd` service 管理

### Changed

- 插件从本地消息协议 demo 推进为可控、可常驻运行的飞书协作入口。

### Verification

- `scripts/smoke-test.sh`
- 真实飞书群 echo 联调
- 真实 `codex exec` bridge 联调
- `launchd start/status/restart/stop` 联调

## [0.1.1] - 2026-05-24

### Added

- Webhook 接收服务与本地自测脚本
- 本地 smoke test
- 私人助理推送配置说明
- 敏感信息发布前扫描脚本
- 贡献说明与发布准备文档

### Verification

- MCP `initialize` / `tools/list`
- Webhook fixtures、自测、签名与解密路径
- 插件结构、脚本权限与配置检查
