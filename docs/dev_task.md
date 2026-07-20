# Dev Task Log

## 2026-07-20 · v1.1.0

### 今日更新

- 明确产品分工：本项目聚焦 Codex 调用飞书原生协作能力；通用远程 Agent 场景推荐 `lark-channel-bridge`。
- 长连接 bot 改为默认拒绝执行，未配置访问控制时不会 spawn 本地命令。
- 新增 Git-aware 项目报告 CLI，覆盖 Docs/Wiki 检索、结构化 Codex 总结、Docx 写回、消息推送和可选 Bitable 记录。
- 稳定 MCP 增加 Docx 创建、块写入、文档 URL 和 Bitable record 工具。
- 统一 `Apache-2.0` 许可证和 `v1.1.0` 版本元数据。
- 更新 README、路线图、工作流、认证、文档和 Bitable 指引。

### 关键边界

- 不新增流式卡片、附件、多 profile 或跨平台 daemon。
- Git 采集只包含提交、状态和 diff stat，不读取完整源码。
- Codex 生成固定使用 `read-only` 和 `ephemeral`。
- 所有真实飞书写入必须显式使用 `--confirm`；Bitable 默认关闭。

### 验证结果

- `bash scripts/smoke-test.sh` 通过。
- `scripts/check-sensitive-values.sh` 通过。
- 未配置访问控制时，本地执行保持关闭，`doctor` 返回退出码 `2`。
- 项目报告 preview、dry run、失败顺序和 MCP 工具路由通过自动化检查。
- 使用标题「Codex Feishu v1.1 验证」完成一次真实私人助理周报推送。
- 当前环境未配置 `FEISHU_USER_ACCESS_TOKEN`，Docs/Wiki 检索、Docx 写回和 Bitable 真实写入留待 UAT 配置后验证；对应模拟链路已通过 smoke test。

## 2026-06-04 · v1.0.0

### 今日更新

- 完成 Feishu bot bridge 的本地闭环验证：
  - 群消息进入
  - 本地 runner 执行
  - 结果回写飞书
- 完成 macOS `launchd` 常驻运行联调：
  - `start`
  - `status`
  - `restart`
  - `stop`
- 补充 bot 诊断能力：
  - `/ids`
  - 更丰富的 `/status`
  - access denied 提示里直接带 allowlist 配置片段
- 补充轻量日报入口：
  - `npm run feishu -- digest --preview`
  - `npm run feishu -- digest --send --confirm`
- 完成默认日报模板中文化，并做了真实飞书推送验证。
- 完成 GitHub 开源文档收口：
  - README 内容结构优化，降低首屏图片占用，突出亮点和快速接入。
  - README、CONTRIBUTING 统一为中文优先，保留必要英文摘要。
  - CHANGELOG 统一以 `1.0.0` 作为首个公开版本。
  - package、插件清单、MCP / Webhook 可见版本同步到 `1.0.0`。
  - 删除独立 release note 和 case study 目录后，将必要信息收口到 CHANGELOG 与 dev task。
- 完成公开文档规则收口：
  - README / CHANGELOG / release notes 只记录用户可感知能力、行为变化、修复、兼容说明和验证证据。
  - 不把不影响用户使用的维护动作写入公开更新日志。

### 今日遇到的问题

1. 飞书消息未进入本地 bot
   原因：本地配置使用了错误的 Feishu `App ID`，并非当前要联调的机器人应用。

2. 同一条飞书消息出现重复回复
   原因：飞书侧存在同一 `message_id` 的重复投递，本地 bot 之前没有幂等保护。

3. 后台常驻与前台联调容易混淆
   原因：`launchd` service 状态、bot 实际收消息状态、Hermes 现有机器人路径在联调阶段容易混在一起。

4. 定时日报需求存在明显维护膨胀风险
   原因：如果直接做完整 `schedule` 子系统，会额外引入第二套 service、状态、日志和调度文档。

5. 默认日报模板内容中文不完整
   原因：结构标题已经中文化，但模板正文仍保留英文示例条目。

6. README 首屏信息过散
   原因：截图和背景说明占用过多篇幅，用户进入仓库后不容易快速理解「能做什么」和「如何接入」。

7. 公开更新日志混入维护动作
   原因：发布收口时把内部文档整理、版本策略说明等内容也写进 CHANGELOG，容易干扰用户判断真实能力变化。

8. 中英文文档维护成本偏高
   原因：完整双语 README 和独立 release note 容易造成重复维护、信息漂移和过期链接。

### 解决方案

1. 更换本地 `.env` 中的 Feishu 应用配置，并重新做长连接联调。
2. 在 bot 中增加基于 `message_id` 的幂等保护，避免重复执行和重复回复。
3. 用统一 CLI、`launchd status`、runner 日志和真实飞书回包来拆分验证层次。
4. 放弃完整 `schedule` 子系统，改为轻量 `digest` 包装脚本，加仓库外 `launchd` 示例。
5. 把默认 `project-update-template.md` 完整改成中文，确保 `digest` 默认输出适合真实私聊推送。
6. 重写 README 首屏结构，优先展示项目定位、核心能力、5 分钟接入和真实功能边界。
7. 将 CONTRIBUTING 改为中文优先、英文补充，降低中文用户贡献门槛。
8. 将 CHANGELOG 改为只保留公开用户可见变化，移除不影响用户的维护动作说明。
9. 将文档结构收口为 README、CHANGELOG、roadmap、pre-release checklist 和 dev task，减少重复来源。

### 验证结果

- `bash scripts/smoke-test.sh` 通过
- `scripts/check-sensitive-values.sh` 通过
- `npm run feishu -- digest --preview` 通过
- `npm run feishu -- digest --send --confirm` 已真实成功
- `npm run feishu -- help` 通过
- README 本地链接与已删除目录引用检查通过
- 相关 GitHub 提交：
  - `c8386e0`
  - `932ce18`
  - `9a5511d`
  - `d98bd85`
  - `05d159b`
  - `c90e853`
  - `2d479ef`

### 明日计划

- 继续收紧访问控制默认值，降低误触发本地执行风险。
- 评估是否需要把日报内容源从固定模板升级为半自动摘要。
- 继续积累已打码截图和真实验证材料，补强开源项目对外证据链。
- 检查 GitHub 首页展示效果，确认 README 首屏、目录和截图在网页端阅读顺畅。
- 做一次从零安装路径复核，重点验证 `.env.example`、权限说明、`doctor` 和 `help` 是否足够引导新用户。
- 梳理下一阶段 `v1.1.0` 的最小增量，优先考虑会话连续性、工作区绑定和更稳定的真实 `codex exec` 对接。
