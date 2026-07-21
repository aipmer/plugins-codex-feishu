# Changelog

所有重要变更统一记录在这里。

## [1.2.0] - 2026-07-21

### Added

- 新增 `npm run feishu -- bitable-bootstrap`，可一键创建 `Codex Project Operations` Base 和 `Project Status` 表。
- `bitable-bootstrap` 支持 `--preview`、`--dry-run-json`、`--confirm`、`--owner`、`--app-token` 和 `--no-write-env`。
- Bootstrap 成功后可自动写入 `FEISHU_PROJECT_NAME`、`FEISHU_PROJECT_OWNER`、`FEISHU_BITABLE_APP_TOKEN` 和 `FEISHU_BITABLE_TABLE_ID` 到本地 `.env`。
- 新增两张 README 图文介绍图，解释私人助理推送和项目报告闭环。

### Changed

- README 和 Bitable reference 改为推荐先用 `bitable-bootstrap` 配置 `report --bitable`。
- README 精简为中文新手优先结构，默认先引导跑通私人助理推送，再进入 Docs/Wiki、Docx 和 Bitable 进阶流程。

### Verification

- `npm run feishu -- bitable-bootstrap --preview --owner "Hunk Wu"`
- `bash scripts/smoke-test.sh`
- `scripts/check-sensitive-values.sh`
- README 图片路径和本地链接检查通过

## [1.1.1] - 2026-07-21

### Added

- 用户身份 OpenAPI 请求在 `FEISHU_USER_ACCESS_TOKEN` 过期时，会自动使用 `FEISHU_USER_REFRESH_TOKEN` 续期并重试原请求。

### Changed

- Bitable 项目状态写入完成真实 UAT，`report --write-doc --bitable --send --confirm` 已验证可创建 Docx、写入 Project Status 记录并发送私聊消息。
- `FEISHU_USER_REFRESH_TOKEN` 成为 Docs/Wiki、Docx 和 Bitable 长时间使用场景的推荐配置。

### Verification

- `bash scripts/smoke-test.sh`
- `scripts/check-sensitive-values.sh`
- 真实飞书 Bitable UAT：Project Status 记录写入成功

## [1.1.0] - 2026-07-20

### Added

- 新增 `npm run feishu -- report` 项目报告工作流：采集 Git 元数据、检索 Docs/Wiki、只读调用 Codex、创建新版 Docx、可选写入 Project Status，并最终发送飞书消息。
- 新增 `npm run feishu -- auth` 本地回调授权流程，自动换取并写入 `FEISHU_USER_ACCESS_TOKEN` / `FEISHU_USER_REFRESH_TOKEN`，避免手动复制授权码过期。
- 稳定 MCP 新增 Docx 创建、文档块写入、文档 URL 查询和 Bitable 单条记录写入工具。
- 报告命令支持 `daily`、`weekly`、`custom`、重复 `--query`、来源上限、结构化 dry run 和显式确认。

### Changed

- 长连接 bot 改为默认拒绝执行；必须配置 owner、admin、允许用户或允许群聊。
- 路线图收口到飞书原生协作，不再追赶流式卡片、附件、多 profile 和跨平台 daemon。
- README 增加与 `lark-channel-bridge` 的场景分工和共存指引。
- 认证文档改为优先推荐本地回调授权，并修正手动 OAuth 脚本路径。
- 项目许可证元数据统一为 `Apache-2.0`。

### Verification

- `bash scripts/smoke-test.sh`
- `scripts/check-sensitive-values.sh`
- `npm run feishu -- report --help`
- 真实飞书私人助理项目报告推送
- 真实飞书 UAT：Docs 搜索、Docx 创建和私聊推送闭环通过

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
