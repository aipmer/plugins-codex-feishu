# Feishu for Codex Roadmap

## 中文路线图

这份路线图基于当前 `Feishu for Codex` 已落地能力，以及对 `lark-coding-agent-bridge` 这类飞书编码助手桥接项目的能力差距分析。

随着 Codex 移动端能力持续增强，`Feishu for Codex` 不应继续把自己定义成「把 Codex 搬进飞书聊天框」的远程替代品。个人即时问答、轻量查看结果这类单人场景，会越来越适合直接在 Codex 官方客户端中完成。

这个插件的产品价值，应该明确收口到团队协作场景：

- 飞书群消息总结与多人可消费的结果回写。
- 项目日报、周报、发布播报和异常提醒。
- Docs / Wiki / Bitable / Webhook 驱动的组织工作流。
- 基于群、私聊、工作区和权限边界的稳定执行入口。

当前插件已经具备：

- 稳定 HTTP-backed MCP：IM、Docs、Wiki、Contacts 基础工具。
- 飞书 OAuth、doctor、smoke test 和本地插件同步脚本。
- 简单长连接机器人：收到群文本后固定回复。
- 项目更新推送脚本：预览、测试发送、确认发送。
- Webhook 接收服务：`url_verification`、签名校验、加密事件解密、事件日志。

后续版本的重点不是继续堆更多 OpenAPI wrapper，也不是和 Codex 移动端竞争通用聊天能力，而是把插件升级成更完整的飞书协作入口：能接收消息、运行 Codex、管理上下文、回写结果，并能长期稳定运行。

## v1.1.0: Codex Message Bridge

目标：把当前固定回复机器人升级为「飞书消息 -> Codex 执行 -> 回复飞书」的最小可用桥接链路，优先验证团队消息触发与结果分发闭环。

### Scope

- 将 `feishu-long-connection-bot.js` 从固定文本回复升级为 Codex 执行入口。
- 支持收到群聊或私聊文本后调用本地 Codex workflow。
- 支持按 `chat_id` 或 `open_id` 隔离基础会话状态。
- 优先支持群聊场景，确保同一个协作现场里的连续对话和结果回写稳定可用。
- 增加最小命令集：
  - `/help`
  - `/new`
  - `/status`
  - `/stop`
  - `/cd <path>`
- 支持默认工作区与当前会话工作区绑定。
- 支持运行中状态记录，避免同一会话重复触发并发任务。
- 在 README 增加「5-Minute Codex Bridge」快速验证流程。

### Acceptance Criteria

- 在飞书测试群发普通文本，机器人能调用本地 Codex 并回复结果。
- 同一群聊连续提问时，能复用该群聊的会话状态。
- `/new` 能重置当前会话。
- `/cd <path>` 能为当前会话切换工作区，并在 `/status` 中显示。
- `/stop` 能终止或标记取消当前执行任务。
- smoke test 覆盖命令解析、会话状态读写和空配置错误提示。

### Out of Scope

- 暂不做流式卡片更新。
- 暂不做图片、文件附件处理。
- 暂不支持多 agent profile。
- 暂不把「个人陪聊式 bot」作为主目标场景。

## v1.2.0: Service, Queue, and Access Control

目标：让插件从「能跑一次」升级为「可以长期运行，并且默认安全」，适合团队固定群、固定工作区和长期协作场景。

### Scope

- 增加统一 CLI 入口，例如 `feishu-codex`：
  - `feishu-codex bot`
  - `feishu-codex webhook`
  - `feishu-codex push`
  - `feishu-codex doctor`
- 增加本地服务管理：
  - `start`
  - `stop`
  - `restart`
  - `status`
- macOS 优先支持 `launchd` 后台运行。
- 增加访问控制：
  - owner
  - admins
  - allowed users
  - allowed chats
- 增加消息队列：
  - 同一会话串行执行。
  - 执行中新增消息进入队列。
  - 可配置短时间批处理窗口。
- 增加错误恢复：
  - Codex 执行失败时给出飞书端可读错误。
  - OpenAPI 失败时输出权限、机器人可见性、应用发布状态等诊断提示。
- 增加本地状态目录说明和迁移策略。
- 增加基础可观测性说明，便于团队排查谁触发了什么任务、失败在哪一层。

### Acceptance Criteria

- 用户可以通过 CLI 启动、停止和查看 bot 状态。
- 配置 owner 后，未授权用户消息不会触发 Codex 执行。
- 同一群短时间连续发多条消息时，不会并发启动多个 Codex 任务。
- 运行错误会返回可读诊断，而不是静默失败。
- smoke test 覆盖 access control、queue、CLI help 和 service config。

### Out of Scope

- 暂不做完整跨平台 daemon 管理。
- 暂不做复杂 Web 管理后台。
- 暂不抽象钉钉、企微或其他平台适配器。

## v1.3.0: Rich Interaction and Attachments

目标：增强飞书端交互体验，让插件更接近团队日常可用的 AI 协作入口。

### Scope

- 支持飞书消息卡片或富文本回复。
- 支持执行状态更新：
  - queued
  - running
  - completed
  - failed
  - cancelled
- 支持图片和文件附件：
  - 接收飞书附件元信息。
  - 下载到本地临时目录。
  - 将本地路径传给 Codex workflow。
- 支持更完整的交互命令：
  - `/config`
  - `/doctor`
  - `/workspace`
  - `/ps`
  - `/timeout`
- 支持多 profile：
  - 不同 Feishu app。
  - 不同 agent 命令。
  - 不同默认工作区。
- 增加真实验证记录模板，鼓励社区提交飞书群总结、项目周报、代码审查等使用经验。

### Acceptance Criteria

- 飞书端可以看到明确的任务状态变化。
- 图片或文件消息可以被下载并传给本地 workflow。
- 用户可以通过命令查看和修改当前会话配置。
- 多 profile 不互相污染状态目录。
- README 和 CHANGELOG 至少覆盖 2 个真实使用流程。

### Out of Scope

- 暂不承诺企业级审计后台。
- 暂不承诺云端托管版本。
- 暂不承诺平台中立 SDK。

## Long-Term Direction

长期方向是把 `Feishu for Codex` 做成团队协作中的稳定 AI 编码入口，而不是单纯的 OpenAPI 工具集合，或 Codex 移动端的聊天替代品。

产品判断：

- 对个人即时问答场景，移动端 Codex 会持续削弱飞书 bot 的独立价值。
- 对团队协作、消息分发、组织上下文和工作流闭环场景，飞书集成价值仍然会持续增强。
- 因此路线图应优先投资「协作基础设施能力」，而不是泛化聊天能力。

优先顺序：

1. 消息桥接到 Codex 执行。
2. 会话连续性与工作区绑定。
3. 后台常驻运行与访问控制。
4. 队列、错误恢复与可观测性。
5. 富交互、附件和多 profile。

暂不建议过早开发多平台适配器。钉钉、企微或其他协作平台应等飞书插件有稳定用户、真实案例和明确复用抽象后再评估。

---

## English Roadmap

This roadmap is based on the current `Feishu for Codex` implementation and the capability gap against Feishu coding-agent bridge projects such as `lark-coding-agent-bridge`.

As Codex mobile becomes more capable, `Feishu for Codex` should not position itself as a remote substitute for the Codex client inside a chat app. Personal quick questions and lightweight follow-ups will increasingly fit the native Codex client better.

The plugin should stay focused on team collaboration workflows:

- summarize group discussions and write results back for multiple readers
- push project digests, release notices, and exception alerts
- power Docs, Wiki, Bitable, and Webhook driven organizational workflows
- provide a stable execution entry point with chat, workspace, and permission boundaries

The plugin already includes:

- Stable HTTP-backed MCP tools for IM, Docs, Wiki, and Contacts.
- Feishu OAuth, doctor checks, smoke tests, and local plugin sync.
- A simple long-connection bot that replies with fixed text.
- A project update push script with preview, test send, and confirmed send modes.
- A webhook receiver with `url_verification`, signature verification, encrypted payload decryption, and event logging.

The next versions should focus on turning the plugin into a real Feishu collaboration entry point: receive messages, run Codex, manage conversation state, send results back, and run reliably over time. They should not compete with Codex mobile on general-purpose chat.

## v1.1.0: Codex Message Bridge

Goal: upgrade the current fixed-reply bot into a minimal Feishu message to Codex execution bridge, with team message triggering and result delivery as the first priority.

### Scope

- Upgrade `feishu-long-connection-bot.js` from fixed replies to a Codex execution entry point.
- Run local Codex workflows from group or private text messages.
- Maintain basic session state by `chat_id` or `open_id`.
- Prioritize group chat continuity so one collaboration thread can keep context and receive shared results.
- Add minimal commands:
  - `/help`
  - `/new`
  - `/status`
  - `/stop`
  - `/cd <path>`
- Support default workspace and per-session workspace binding.
- Track running state to avoid duplicate concurrent tasks in the same session.
- Add a `5-Minute Codex Bridge` quickstart to the README.

### Acceptance Criteria

- A message in a Feishu test group can trigger local Codex execution and receive a reply.
- Follow-up messages in the same group can reuse the group session state.
- `/new` resets the current session.
- `/cd <path>` changes the current workspace and `/status` displays it.
- `/stop` terminates or marks the current run as cancelled.
- Smoke tests cover command parsing, session state, and missing configuration diagnostics.

### Out of Scope

- No streaming cards yet.
- No image or file attachments yet.
- No multi-agent profile support yet.
- No attempt to optimize for personal chat companion scenarios yet.

## v1.2.0: Service, Queue, and Access Control

Goal: make the plugin safe and stable enough to run continuously in fixed team chats and bound workspaces.

### Scope

- Add a unified CLI entry point, for example `feishu-codex`:
  - `feishu-codex bot`
  - `feishu-codex webhook`
  - `feishu-codex push`
  - `feishu-codex doctor`
- Add local service management:
  - `start`
  - `stop`
  - `restart`
  - `status`
- Prioritize macOS `launchd` support for background running.
- Add access control:
  - owner
  - admins
  - allowed users
  - allowed chats
- Add a message queue:
  - serialize execution per session
  - queue new messages while a run is active
  - support a configurable short batching window
- Add failure recovery:
  - user-readable Feishu replies for Codex failures
  - diagnostics for OpenAPI permission, bot visibility, and app publish status problems
- Document the local state directory and migration strategy.
- Add basic observability guidance so teams can inspect who triggered what and where failures happened.

### Acceptance Criteria

- Users can start, stop, and inspect bot status from the CLI.
- Unauthorized users cannot trigger Codex execution when owner access is configured.
- Multiple rapid messages in one group do not start concurrent Codex runs.
- Runtime failures produce readable diagnostics instead of silent failures.
- Smoke tests cover access control, queue behavior, CLI help, and service config.

### Out of Scope

- No full cross-platform daemon manager yet.
- No web admin dashboard yet.
- No DingTalk, WeCom, or multi-platform adapter abstraction yet.

## v1.3.0: Rich Interaction and Attachments

Goal: improve the Feishu-side interaction quality so the plugin feels usable in real team workflows.

### Scope

- Support Feishu message cards or rich text replies.
- Support task state updates:
  - queued
  - running
  - completed
  - failed
  - cancelled
- Support image and file attachments:
  - read attachment metadata
  - download attachments to a local temporary directory
  - pass local paths to Codex workflows
- Add richer commands:
  - `/config`
  - `/doctor`
  - `/workspace`
  - `/ps`
  - `/timeout`
- Support multiple profiles:
  - different Feishu apps
  - different agent commands
  - different default workspaces
- Add real verification-note templates for chat summaries, project digests, code review, and team support workflows.

### Acceptance Criteria

- Feishu users can see clear task state updates.
- Image or file messages can be downloaded and passed into a local workflow.
- Users can inspect and update session configuration through commands.
- Multiple profiles do not share or corrupt each other's state directories.
- README and case studies cover at least two real workflows.

### Out of Scope

- No enterprise audit dashboard yet.
- No hosted cloud service yet.
- No platform-neutral SDK yet.

## Long-Term Direction

The long-term direction is to make `Feishu for Codex` a stable AI coding entry point for team collaboration, not just a collection of OpenAPI tools or a chat substitute for Codex mobile.

Product view:

- Codex mobile will keep reducing the standalone value of a Feishu bot for personal quick questions.
- Feishu integration still gains value in team collaboration, shared context, notifications, and workflow closure.
- The roadmap should therefore invest in collaboration infrastructure instead of generic chat breadth.

Priority order:

1. Bridge Feishu messages to Codex execution.
2. Add session continuity and workspace binding.
3. Add background service support and access control.
4. Add queues, failure recovery, and observability.
5. Add rich interaction, attachments, and multiple profiles.

Do not start multi-platform adapter work too early. DingTalk, WeCom, or other collaboration platforms should be revisited only after Feishu has stable users, real case studies, and clear reusable abstractions.
