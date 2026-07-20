# Bitable Project Templates

Use case: sync Codex project status, tasks, risks, release records, or case study intake into Feishu Base/Bitable.

## Template 1: Project Status

Minimum required fields:

- `Project`
- `Status`
- `Owner`

Fields:

- `Project`: text
- `Status`: single select, values `Todo`, `In Progress`, `Blocked`, `Done`
- `Owner`: text
- `Next Step`: text
- `Updated At`: date

Example record:

```yaml
Project: "Feishu for Codex"
Status: "In Progress"
Owner: "Hunk Wu"
Next Step: "Ship weekly private assistant update flow"
Updated At: "2026-05-25"
```

## Template 2: Release Records

Minimum required fields:

- `Version`
- `Date`
- `Summary`

Fields:

- `Version`: text
- `Date`: date
- `Summary`: text
- `Verification`: text
- `Git Commit`: text
- `Release Note URL`: url

Example record:

```yaml
Version: "v1.1.0"
Date: "2026-07-20"
Summary: "Added a Feishu-native project report workflow."
Verification: "scripts/smoke-test.sh"
Git Commit: "abc1234"
Release Note URL: "https://example.com/changelog#100"
```

## Template 3: Risk Tracker

Minimum required fields:

- `Risk`
- `Severity`
- `Status`

Fields:

- `Risk`: text
- `Severity`: single select, values `Low`, `Medium`, `High`
- `Mitigation`: text
- `Owner`: text
- `Status`: single select, values `Open`, `Watching`, `Resolved`

Example record:

```yaml
Risk: "Tenant permissions may block document import."
Severity: "High"
Mitigation: "Add a permission checklist to setup docs."
Owner: "Hunk Wu"
Status: "Open"
```

## Template 4: Case Study Intake

Minimum required fields:

- `Submitter`
- `Project`
- `Workflow`
- `Permission To Publish`

Fields:

- `Submitter`: text
- `Project`: text
- `Workflow`: text
- `Result`: text
- `Permission To Publish`: checkbox
- `Notes`: text

Example record:

```yaml
Submitter: "Anonymous Builder"
Project: "Internal AI delivery bot"
Workflow: "Private assistant weekly updates"
Result: "Reduced manual reporting work"
Permission To Publish: true
Notes: "Needs customer details redacted before publication."
```

## Create Base

```yaml
tool: mcp__feishu-mcp__bitable_v1_app_create
data:
  name: "Codex Project Operations"
  time_zone: "Asia/Shanghai"
useUAT: true
```

## Create Record

```yaml
tool: mcp__feishu-mcp__bitable_v1_appTableRecord_create
path:
  app_token: "bascnxxxxxx"
  table_id: "tblxxxxxx"
data:
  fields:
    Project: "Feishu for Codex"
    Status: "In Progress"
    Owner: "Hunk Wu"
    Next Step: "Ship private assistant push workflow"
```

## Minimum Permissions

- Bitable read/write workflows require Bitable permissions approved for the target tenant.
- Use `useUAT: true` when the current user should own or directly open the Base.
- Use placeholders in docs and examples. Do not commit real `app_token`, `table_id`, record IDs, user IDs, or tenant data.

Current boundary:

- This stage delivers project operation templates and integration patterns.
- It does not promise a full Base ORM, sync engine, or generic multi-table framework.

## 中文说明

### 用途

这个示例适合把 Codex 项目状态、任务、风险、发布记录或案例征集结果同步到飞书 Base / 多维表格。

### 模板 1：Project Status

最小必填字段：

- `Project`
- `Status`
- `Owner`

字段含义：

- `Project`：项目名
- `Status`：当前状态
- `Owner`：负责人
- `Next Step`：下一步动作
- `Updated At`：最近更新时间

### 模板 2：Release Records

最小必填字段：

- `Version`
- `Date`
- `Summary`

适合记录版本、发布日期、验证结果、commit 和 release note 链接。

### 模板 3：Risk Tracker

最小必填字段：

- `Risk`
- `Severity`
- `Status`

适合持续记录风险项、缓解动作、责任人和处理状态。

### 模板 4：Case Study Intake

最小必填字段：

- `Submitter`
- `Project`
- `Workflow`
- `Permission To Publish`

适合收集社区投稿案例，并提前确认是否允许公开发布。

### Base 创建与写入

可以先创建一个 `Codex Project Operations` Base，再逐张表扩展。
写记录时，优先先保证字段名、字段类型和示例记录一致，再考虑后续自动化。

### 最小权限与当前边界

- Bitable 读写需要租户审批通过的 Base 权限
- 如果 Base 需要当前用户直接打开，使用 `useUAT: true`
- 示例里统一用占位值，不提交真实 `app_token`、`table_id` 或记录 ID

当前边界：

- 这一阶段交付的是项目运营模板和接入范式
- 不承诺完整 Base ORM、同步引擎或通用多表框架
