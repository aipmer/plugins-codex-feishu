# Dev Task Log

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

### 解决方案

1. 更换本地 `.env` 中的 Feishu 应用配置，并重新做长连接联调。
2. 在 bot 中增加基于 `message_id` 的幂等保护，避免重复执行和重复回复。
3. 用统一 CLI、`launchd status`、runner 日志和真实飞书回包来拆分验证层次。
4. 放弃完整 `schedule` 子系统，改为轻量 `digest` 包装脚本，加仓库外 `launchd` 示例。
5. 把默认 `project-update-template.md` 完整改成中文，确保 `digest` 默认输出适合真实私聊推送。

### 验证结果

- `bash scripts/smoke-test.sh` 通过
- `scripts/check-sensitive-values.sh` 通过
- `npm run feishu -- digest --preview` 通过
- `npm run feishu -- digest --send --confirm` 已真实成功
- 相关 GitHub 提交：
  - `c8386e0`
  - `932ce18`
  - `9a5511d`
  - `d98bd85`

### 后续待办

- 继续收紧访问控制默认值，降低误触发本地执行风险。
- 评估是否需要把日报内容源从固定模板升级为半自动摘要。
- 继续积累已打码截图、真实回包和案例，补强开源项目对外证据链。
