# Feishu Group -> Codex Execution -> Reply

## English

### Summary

- Builder: maintainer
- Project: `Feishu for Codex`
- Audience: small teams using Feishu as the main collaboration surface
- Timeframe: one focused implementation cycle
- Result: local Feishu group messages can trigger a queued Codex workflow and return readable replies

### Starting Point

The original bot path only proved that a Feishu long-connection app could receive a group text message and send back a fixed reply. That was enough for protocol validation, but not enough for a real collaboration assistant.

The goal was to turn that path into a minimal but credible workflow:

- a message arrives in a Feishu group
- the bot decides whether the sender or chat is allowed
- the message is turned into a local Codex-compatible payload
- local execution runs in a bound workspace
- the result is written back into the same group

### Constraints

- Time: ship a beta path quickly without rewriting the plugin architecture
- Existing codebase: already had HTTP-backed MCP, webhook support, and a simple long-connection bot
- Team: maintainer-driven implementation
- Platform: local self-hosted first, macOS preferred for service management

### Codex Workflow

Codex handled:

- refactoring the bot from static reply to execution bridge
- adding session state, queueing, access control, and service scaffolding
- writing runner and echo helpers for a stable local protocol
- expanding smoke coverage to include end-to-end bridge checks

Manual work still mattered for:

- deciding product scope and release sequencing
- defining what should ship in beta versus later
- planning the real-device and real-Feishu handoff

### Feishu / Collaboration Workflow

- Group message intake: uses Feishu long connection instead of public webhook setup for the fastest local verification path
- Session isolation: one chat keeps its own workspace, queue, and last task state
- Access control: owner, admins, allowed users, and allowed chats can be enforced before execution
- Queueing: when multiple messages arrive in one group, execution stays serial and messages are not dropped
- Reply path: results, queue notices, cancellations, and failures are all written back into the same group

### What Shipped

- Unified CLI entry
- Feishu-to-Codex runner contract
- Echo-based local verification path
- Access control
- Serial queue with optional batching window
- Duplicate Feishu message delivery guard
- macOS-first `launchd` service operations
- Smoke coverage for bridge, queue, CLI, and service config

### Result

- The plugin moved from “message protocol demo” to “local collaboration assistant beta.”
- The repo now has a repeatable local verification story for both echo and real `codex exec` execution.
- Release preparation became clearer because bridge, queue, duplicate-message handling, and service layers are now testable separately.

### Lessons

- A good Feishu assistant is not just “chat with Codex in another window.”
- The real value starts when group context, workspace binding, queueing, and operational control are treated as first-class features.
- A repo-provided runner is worth the extra file because it stabilizes the contract between chat input and local execution.

### What To Improve

- Add richer status feedback so users can see queued, running, and failed states more clearly.
- Add richer release evidence with redacted screenshots and service status captures.

---

## 中文

### 摘要

- 作者：维护者
- 项目：`Feishu for Codex`
- 目标用户：把飞书作为主协作界面的轻量团队
- 时间周期：一轮集中实现
- 结果：本地飞书群消息已经可以触发带队列的 Codex 工作流，并把可读结果回写到群里

### 起点

最初的 bot 只证明了一件事：飞书长连接应用可以收到群文本消息，再返回固定回复。这个路径足够验证协议，但离真实协作助手还差很远。

这一轮的目标，是把它推进成最小但可信的 workflow：

- 群里来一条消息
- bot 先判断用户或群是否有权限
- 再把消息转成兼容本地 Codex 的 payload
- 在绑定工作区里执行本地任务
- 最后把结果回写到同一个群

### 约束

- 时间：要尽快形成 beta，可上线验证，但不能重写整套架构
- 现有代码：已经有 HTTP-backed MCP、webhook 支持和简单长连接 bot
- 团队：以维护者主导实现
- 平台：先做本地 self-hosted，service 管理优先照顾 macOS

### Codex 工作流

Codex 主要负责：

- 把 bot 从静态回复重构成执行 bridge
- 增加会话状态、队列、访问控制和 service 骨架
- 写 runner 和 echo 辅助脚本，稳定本地协议
- 扩展 smoke 覆盖到 bridge 端到端验证

仍然需要手工判断的部分：

- 产品边界和版本节奏
- 哪些能力适合 beta，哪些该留到后续版本
- 真实设备和真实飞书联调时机

### 飞书 / 协作工作流

- 群消息接入：本地验证阶段优先使用 Feishu 长连接，而不是先搭公网 webhook
- 会话隔离：同一个群保留自己的工作区、队列和最近任务状态
- 访问控制：可以在执行前限制 owner、admins、allowed users、allowed chats
- 队列：同一个群连续来多条消息时，执行保持串行，不丢消息
- 回复链路：结果、排队提示、取消和失败提示都会回写到同一个群

### 实际上线内容

- 统一 CLI 入口
- Feishu 到 Codex 的 runner 协议
- 基于 echo 的本地验证路径
- 访问控制
- 串行队列和可选批处理窗口
- 飞书重复消息投递保护
- macOS 优先的 `launchd` service 运维能力
- bridge、queue、CLI、service config 的 smoke 验证

### 结果

- 插件已经从“消息协议 demo”推进到“本地协作助手 beta”。
- 仓库具备了 echo 和真实 `codex exec` 两条可重复验证路径。
- 发布准备更清晰了，因为 bridge、queue、重复消息处理和 service 现在都能独立测试。

### 经验

- 一个好用的飞书助手，不只是“把 Codex 搬到另一个聊天窗口里”。
- 真正的价值来自群上下文、工作区绑定、排队执行和运维可控性。
- 仓库内置 runner 很值得做，因为它稳定了聊天输入和本地执行之间的契约。

### 下次会怎么改

- 增强状态反馈，让用户更清楚看到 queued、running、failed
- 补充已打码截图和 service status 证据链
