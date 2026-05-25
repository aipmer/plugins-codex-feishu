# Bitable Project Templates

Use case: sync Codex project status, tasks, risks, release records, or case study intake into Feishu Base/Bitable.

## Template 1: Project Status

Fields:

- `Project`: text
- `Status`: single select, values `Todo`, `In Progress`, `Blocked`, `Done`
- `Owner`: text
- `Next Step`: text
- `Updated At`: date

## Template 2: Release Records

Fields:

- `Version`: text
- `Date`: date
- `Summary`: text
- `Verification`: text
- `Git Commit`: text
- `Release Note URL`: url

## Template 3: Risk Tracker

Fields:

- `Risk`: text
- `Severity`: single select, values `Low`, `Medium`, `High`
- `Mitigation`: text
- `Owner`: text
- `Status`: single select, values `Open`, `Watching`, `Resolved`

## Template 4: Case Study Intake

Fields:

- `Submitter`: text
- `Project`: text
- `Workflow`: text
- `Result`: text
- `Permission To Publish`: checkbox
- `Notes`: text

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
