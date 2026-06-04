# Feishu for Codex Pre-Release Checklist

这份清单面向 `v1.0.0` 及之后的版本发布前联调。目标不是只确认代码能跑，而是确认：

- 真实飞书消息链路可用
- 本地 service 管理可用
- 访问控制、队列和状态反馈符合预期
- README、CHANGELOG、dev_task 与真实行为一致

---

## 0. 发布前静态检查

必须通过：

```bash
bash scripts/smoke-test.sh
```

确认项：

- 插件 JSON、脚本权限、MCP 协议检查通过
- bridge / runner / queue / CLI / service config 检查通过
- 未误提交真实飞书 ID、token、secret

建议额外确认：

- `git status --short` 中没有无关调试文件
- `.env` 没有被误提交
- 新文档入口是否已经加入 README 或索引

---

## 1. Echo Bridge 联调

目标：先验证 `message -> bot -> runner -> reply`，不引入真实 Codex 执行变量。

### 配置

`.env` 至少包含：

```env
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx
FEISHU_DEFAULT_WORKSPACE=/absolute/path/to/your/workspace
FEISHU_CODEX_COMMAND="node plugins/feishu/scripts/feishu-codex-runner.js"
FEISHU_RUNNER_COMMAND="node plugins/feishu/scripts/feishu-codex-echo.js"
FEISHU_CODEX_COMMAND_MODE=env
FEISHU_BOT_ALLOWED_CHATS=oc_xxxxx
```

### 执行

```bash
npm run feishu -- doctor
npm run feishu -- bot
```

### 验收

- bot 正常启动，没有凭证或权限报错
- 飞书测试群发普通文本后，机器人回出：
  - `Feishu Codex Echo`
  - `Session: chat:...`
  - `Workspace: ...`
  - `Message: ...`
- `/status` 返回当前工作区、队列长度、运行状态
- 未授权群或未授权用户不会触发本地执行

### 证据

- 一张 bot 启动终端截图
- 一张飞书群内 echo 回复截图

---

## 2. Real Codex Bridge 联调

目标：验证真实下游命令，而不是只验证 echo。

### 配置

把 `.env` 中：

```env
FEISHU_RUNNER_COMMAND="codex exec"
```

如果需要，也可以替换成你本机当前可用的实际命令包装。

### 建议测试消息

按这个顺序发：

1. `请总结当前项目目录的主要结构`
2. `请继续，列出最重要的 3 个脚本`
3. `请说明当前 service 管理能力`

### 验收

- 第一条消息能收到真实执行结果
- 同一群连续发 3 条消息时，不会并发启动多个本地任务
- 队列提示会显示 `Queued: N`
- 队列 drain 完成后，后续回复顺序和内容可解释
- `/stop` 能取消当前任务
- `/new` 能在非运行态下重置当前会话
- 同一 `message_id` 重复投递时不会重复执行或重复回复

### 失败时要记录

- 是权限失败、命令失败、超时还是工作区错误
- 飞书端提示是否足够可读
- `stdout.log` / `stderr.log` 中是否能定位原因

### 证据

- 一段真实桥接成功的飞书对话截图
- 一段连续 2 到 3 条消息排队执行的截图

---

## 3. launchd Service 联调

目标：验证后台常驻闭环，而不是只验证 plist 能生成。

### 执行

```bash
npm run feishu -- start
npm run feishu -- status
npm run feishu -- restart
npm run feishu -- stop
```

### 验收

- `start` 后：
  - 生成 `service/launchd.plist`
  - 生成 `service/service.json`
  - 生成或更新 `service/stdout.log`
  - 生成或更新 `service/stderr.log`
- `status` 能显示：
  - `Service label`
  - `Launchctl loaded`
  - `Launchctl state`
  - `PID`
  - 日志路径
- `restart` 后服务仍可正常响应飞书消息
- `stop` 后状态变为 stopped，且不会继续处理新消息

### 额外检查

- `service.json` 中 `last_started_at` / `last_stopped_at` 更新合理
- 停止服务后，bot state 内遗留的 `running` 状态会被清掉

### 证据

- `start` 和 `status` 终端截图
- `service/` 目录文件截图

---

## 4. 访问控制联调

目标：确认“默认安全”已经成立。

### 推荐最小配置

```env
FEISHU_BOT_OWNER_OPEN_ID=ou_owner
FEISHU_BOT_ALLOWED_CHATS=oc_test_chat
```

### 验收

- owner 在允许群中可以正常触发执行
- 非 owner 且不在 `allowed users` / `admins` 的用户，会收到拒绝提示
- 允许群可以放行消息
- 非允许群不会触发真实执行

### 证据

- 一张授权成功截图
- 一张拒绝提示截图

---

## 5. 队列与批处理联调

目标：确认串行和可选批处理窗口符合预期。

### 串行队列

设置：

```env
FEISHU_BOT_BATCH_WINDOW_MS=0
```

验证：

- 连续快速发送 3 条消息
- 当前运行消息之外，其余消息进入队列
- 每条队列消息都能按顺序收到结果

### 批处理窗口

设置：

```env
FEISHU_BOT_BATCH_WINDOW_MS=500
```

验证：

- 在 500ms 内连续发 2 条短消息
- 这两条消息会合并为一个队列批次
- 回复里能看出是合并执行，而不是两次完全独立执行

### 证据

- 一张串行排队截图
- 一张批处理窗口合并结果截图

---

## 6. 文档与发布物检查

发布前需要同时更新：

- `README.md`
- `CHANGELOG.md`
- `docs/dev_task.md`

确认项：

- CLI 示例命令与当前实现一致
- `.env.example` 与 README 配置项一致
- service 管理边界写清楚：
  - macOS `launchd` only
  - local self-hosted
  - text messages first
- 文档中的能力描述与真实联调证据一致

---

## 7. 建议发布顺序

推荐按这个顺序完成：

1. 通过 `scripts/smoke-test.sh`
2. 跑通 echo bridge
3. 跑通真实 `codex exec`
4. 跑通 `launchd start/status/restart/stop`
5. 补截图和证据
6. 检查 README、CHANGELOG 与 dev_task
7. 发布 `v1.0.0`

---

## 8. 发布门槛

满足以下条件，才建议发 `v1.0.0`：

- 本地 smoke 全通过
- 真实飞书群 echo 联调通过
- 真实飞书群 Codex bridge 联调通过
- `launchd` 服务管理联调通过
- 至少有一条授权拒绝路径被验证
- 至少有一条串行排队路径被验证
- 重复消息幂等保护已通过本地测试
- README、CHANGELOG 与 dev_task 已更新

如果以上任一项没有证据，建议不要直接发正式 beta。
