# Feishu for Codex Roadmap

## 中文路线图

### 产品边界

Feishu for Codex 聚焦「让 Codex 使用飞书组织数据和协作能力」：读取 IM、Docs、Wiki 和 Bitable，结合项目上下文生成结果，再写回飞书。

需要在飞书聊天中远程操作本机 Claude Code 或 Codex CLI，并使用流式卡片、附件、多 profile 或跨平台后台服务时，推荐使用 [lark-channel-bridge](https://github.com/zarazhangrui/lark-coding-agent-bridge)。本项目不引入该项目作为依赖，也不重复建设它已经成熟覆盖的通用 Agent Bridge 能力。

### v1.0.0 已完成

- 飞书消息到本地 Codex runner 的文本 Bridge。
- 按会话隔离的状态、工作区、串行队列和幂等保护。
- `/help`、`/new`、`/status`、`/ids`、`/stop`、`/cd`。
- owner、admin、用户和群聊访问控制。
- macOS `launchd` 的 start、stop、restart 和 status。
- 私人助理推送、日报模板、Webhook 和稳定 HTTP MCP。

### v1.1.0 飞书原生项目报告

- 默认拒绝未配置访问控制的本地执行。
- 自动采集 Git 进展，按关键词检索飞书 Docs/Wiki。
- 使用只读 Codex 执行生成结构化中文项目报告。
- 将结果创建为用户持有的新版飞书文档。
- 可选写入 Project Status 多维表格，最后推送飞书消息。
- 所有真实写入必须显式使用 `--confirm`。

### 后续优先级

1. 项目报告的真实案例和首次配置体验。
2. Docs/Wiki 检索质量、来源选择和权限诊断。
3. Project Status、Release Records、Risk Tracker 的可复用自动化。
4. 群聊决策、发布通知和异常提醒工作流。
5. 在重复需求明确后再评估钉钉或企微，不考虑 QQ。

### 明确不做

- 不追赶流式卡片、COT 展示、图片或文件代理。
- 不建设多 Agent、多 profile 或平台中立 Bridge SDK。
- 不扩展第二套跨平台 daemon 或完整调度系统。
- 不承诺 Base ORM、通用同步引擎或企业审计后台。

---

## English Roadmap

### Product Boundary

Feishu for Codex focuses on letting Codex use Feishu organizational context and collaboration APIs: read IM, Docs, Wiki, and Bitable data, combine it with project context, and write useful results back to Feishu.

For remote control of local Claude Code or Codex CLI from Feishu chat, including streaming cards, attachments, multiple profiles, and cross-platform services, use [lark-channel-bridge](https://github.com/zarazhangrui/lark-coding-agent-bridge). This project does not depend on it and will not duplicate its general-purpose agent bridge runtime.

### Shipped In v1.0.0

- Text message bridge from Feishu to a local Codex runner.
- Per-session state, workspaces, serialized queues, and delivery deduplication.
- Minimal chat commands and explicit access control.
- macOS launchd service management.
- Private assistant push, digest templates, Webhook receiver, and stable HTTP MCP.

### v1.1.0 Feishu-Native Project Reports

- Fail closed when bot access control is not configured.
- Collect Git progress and retrieve relevant Feishu Docs/Wiki context.
- Generate a structured Chinese report through read-only Codex execution.
- Write the result to a user-owned Feishu Docx document.
- Optionally create a Project Status Bitable record, then send the final message.
- Require `--confirm` for every real write.

### Next Priorities

1. Real project-report case studies and first-run setup quality.
2. Better knowledge-source selection and permission diagnostics.
3. Reusable Project Status, Release Records, and Risk Tracker automation.
4. Group decision, release notification, and exception alert workflows.
5. Revisit DingTalk or WeCom only after repeated demand; QQ remains out of scope.

### Explicit Non-Goals

- Streaming cards, COT presentation, and attachment proxying.
- Multi-agent profiles or a platform-neutral bridge SDK.
- A second cross-platform daemon or full scheduling subsystem.
- A Base ORM, generic sync engine, or enterprise audit console.
