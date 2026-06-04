# Platform Roadmap

## English

Feishu for Codex should stay focused on the Feishu ecosystem for the next one or two releases.

### Current Direction

- v1.1: private assistant push, project digest previews, setup diagnostics, Docs/Wiki retrieval, and write-back workflows.
- v1.2: Feishu Base/Bitable workflows for project status, tasks, risks, release records, and community case intake.
- Community growth: real case studies, practical setup notes, and contributor workflows around Feishu + Codex.

### Platform Decision

Do not build DingTalk, WeCom, or QQ adapters yet.

- DingTalk and WeCom are valid enterprise collaboration platforms, but they bring separate app models, permissions, event delivery, bot behavior, and documentation surfaces.
- QQ is less aligned with this plugin's current B2B collaboration and project workflow positioning.
- A platform-neutral SDK should wait until the Feishu plugin has stable users, repeatable case studies, and clear adapter requirements.

### Revisit Criteria

Revisit multi-platform support when at least two of these are true:

- Feishu v1.1/v1.2 workflows are stable and documented.
- There are public case studies from real users.
- Multiple users ask for the same DingTalk or WeCom workflow.
- The shared abstraction is obvious from real usage, not from speculative design.

## 中文

Feishu for Codex 后续一到两个版本建议继续聚焦飞书生态。

### 当前方向

- v1.1：私人助理推送、项目更新预览、配置诊断、Docs/Wiki 检索和写回流程。
- v1.2：飞书 Base / 多维表格，用于项目状态、任务、风险、发布记录和社区案例收集。
- 社区增长：围绕 Feishu + Codex 沉淀真实案例、配置指引和贡献流程。

### 平台决策

暂不正式开发钉钉、企微或 QQ 适配器。

- 钉钉和企微都是有效的企业协作平台，但会引入独立的应用模型、权限体系、事件投递、机器人行为和文档体系。
- QQ 与当前插件的 B 端协作和项目 workflow 定位不完全一致。
- 平台中立 SDK 应该等飞书插件有稳定用户、真实案例和明确适配需求后再抽象。

### 重新评估条件

满足以下至少两项时，再重新评估多平台支持：

- 飞书 v1.1/v1.2 workflow 已稳定并完成文档化。
- 已有真实用户公开案例。
- 多个用户提出相同的钉钉或企微 workflow 需求。
- 从真实使用中看到了明确的公共抽象，而不是提前设计出来的抽象。
