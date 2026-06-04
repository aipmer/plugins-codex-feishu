# Feishu for Codex 贡献指南

欢迎一起改进 Feishu for Codex。这个项目欢迎来自 Codex、飞书、MCP、智能体 workflow 实战中的具体贡献。

[English](#english)

## 可以贡献什么

优先欢迎高信号内容：

- 飞书 workflow 改进：IM、Docs、Wiki、多维表格、Webhook、权限、OAuth 流程。
- MCP 运行时修复：tool schema、错误处理、token mode、本地诊断和 smoke test。
- AI 调优技巧：真实项目里有效的 prompt、agent instructions、workflow 模式或评估方法。
- 踩坑实录：安装失败、权限问题、token 问题、飞书控制台配置、恢复步骤。
- `AGENTS.md` 规则：你自己项目中让 Codex 表现更好的简洁规则。
- 真实验证记录：包括有效做法、失败点、验证路径和已知边界。

请避免：

- 提交密钥、token、私有聊天记录、私有文档，或包含敏感租户数据的截图。
- 没有明确 bug、场景或维护收益的大范围重构。
- 对用户安装、调试、构建没有帮助的纯营销文案。

## PR 提交流程

1. 大改动、新工具族或行为变更，先开 issue 说明背景。
2. 保持 PR 聚焦。文档修复、运行时修复、工作流说明通常应拆成不同 PR。
3. 提交前运行：

```bash
scripts/smoke-test.sh
```

4. 代码改动请说明：
   - 改了什么
   - 为什么改
   - 如何验证
   - 是否需要额外飞书权限或租户配置
5. 文档改动请确认链接使用相对路径，示例不暴露私有 ID。
6. 截图请打码租户名、用户名、群 ID、文档标题和 token。

## 建议 PR 模板

```md
## Summary

-

## Verification

- [ ] `scripts/smoke-test.sh`
- [ ] Manual Feishu verification, if applicable:

## Notes

- Required permissions:
- Known limitations:
```

## 验证说明

如果你提交文档或 workflow 说明，优先补充这些信息：

- 改了什么
- 在什么环境下验证
- 如何验证
- 涉及哪些权限或租户设置
- 还有哪些已知限制

---

## English

# Contributing to Feishu for Codex

Thanks for helping improve Feishu for Codex. This project welcomes practical contributions from people building with Codex, Feishu, MCP, and agent workflows.

## What To Contribute

High-signal contributions are preferred:

- Feishu workflow improvements: IM, Docs, Wiki, Bitable, Webhook, permissions, or OAuth flows.
- MCP runtime fixes: tool schemas, error handling, token modes, local diagnostics, and smoke tests.
- AI tuning tips: prompts, agent instructions, workflow patterns, or evaluation notes that worked in real projects.
- Troubleshooting notes: install failures, permission gotchas, token issues, Feishu console settings, and recovery steps.
- `AGENTS.md` rules: concise project rules that helped Codex work better in your own repo.
- Real verification notes: practical writeups about what worked, what failed, and how the behavior was verified.

Please avoid:

- Secrets, tokens, private chat logs, private documents, or screenshots with sensitive tenant data.
- Broad rewrites without a concrete bug, use case, or maintenance benefit.
- Pure marketing copy that does not help users install, debug, or build.

## Pull Request Process

1. Open an issue first for large changes, new tool families, or behavior changes.
2. Keep PRs focused. A docs fix, a runtime fix, and a workflow note should usually be separate PRs.
3. Run the smoke test before submitting:

```bash
scripts/smoke-test.sh
```

4. For code changes, include:
   - What changed
   - Why it changed
   - How you verified it
   - Any Feishu permission or tenant requirement
5. For docs changes, make sure links are relative and examples do not expose private IDs.
6. For screenshots, redact tenant names, user names, chat IDs, document titles, and tokens.

## Suggested PR Template

```md
## Summary

-

## Verification

- [ ] `scripts/smoke-test.sh`
- [ ] Manual Feishu verification, if applicable:

## Notes

- Required permissions:
- Known limitations:
```

## Verification Notes

If you submit docs or workflow notes, prefer concrete evidence:

- What changed?
- What environment was used?
- How was it verified?
- Which permissions or tenant settings mattered?
- What remains a known limitation?
