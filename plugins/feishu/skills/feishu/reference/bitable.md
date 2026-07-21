# Bitable

## Recommended Bootstrap

Use the built-in bootstrap command first when you only need the standard `Project Status` table for `report --bitable`:

```bash
npm run feishu -- bitable-bootstrap --preview --owner "Your Name"
npm run feishu -- bitable-bootstrap --confirm --owner "Your Name"
```

The command creates a user-owned Base and `Project Status` table with these fields:

- `Project`: text
- `Status`: single select, values `Todo`, `In Progress`, `Blocked`, `Done`
- `Owner`: text
- `Next Step`: text
- `Updated At`: date time

By default it writes these values to the local `.env` file:

```env
FEISHU_PROJECT_NAME=Feishu for Codex
FEISHU_PROJECT_OWNER=Your Name
FEISHU_BITABLE_APP_TOKEN=bascn_xxxxx
FEISHU_BITABLE_TABLE_ID=tbl_xxxxx
```

Use `--app-token` when you want to create the table in an existing Base. Use `--no-write-env` when you only want the returned IDs.

## Create Base

```yaml
tool: mcp__feishu-mcp__bitable_v1_app_create
data:
  name: "Codex Tasks"
  time_zone: "Asia/Shanghai"
useUAT: true
```

Use `useUAT: true` when the user must open the Base directly.

## Create Table

```yaml
tool: mcp__feishu-mcp__bitable_v1_appTable_create
path:
  app_token: "bascnxxxxxx"
data:
  table:
    name: "Tasks"
    default_view_name: "Default"
    fields:
      - field_name: "Title"
        ui_type: "Text"
      - field_name: "Status"
        ui_type: "SingleSelect"
        property:
          options:
            - name: "Todo"
            - name: "Done"
```

## Search Records

```yaml
tool: mcp__feishu-mcp__bitable_v1_appTableRecord_search
path:
  app_token: "bascnxxxxxx"
  table_id: "tblxxxxxx"
params:
  page_size: 20
data:
  filter:
    conjunction: and
    conditions:
      - field_name: "Status"
        operator: is
        value:
          - "Todo"
```

Filter `value` should be an array.

## Create Record

```yaml
tool: mcp__feishu-mcp__bitable_v1_appTableRecord_create
path:
  app_token: "bascnxxxxxx"
  table_id: "tblxxxxxx"
data:
  fields:
    Title: "Ship Feishu plugin MVP"
    Status: "Todo"
```

## Project Operation Templates

Recommended project operation tables:

- Project status
- Release records
- Risk tracker
- Case study intake

See `examples/bitable-project-templates.md` for fields and record examples.

Recommended first two tables:

- `Project Status`: the fastest way to track ongoing work, owners, and next steps.
- `Release Records`: the fastest way to preserve verification results and release evidence.

Current wrapper boundary:

- Project Status record creation is available through `bitable_v1_appTableRecord_create`.
- For other Bitable endpoints, use `feishu_openapi_request` as the transition path.
- The current stage focuses on reusable project operation templates, not a full Base abstraction layer.

## 中文说明

### 创建 Base

推荐先用内置命令创建标准 Project Status 表：

```bash
npm run feishu -- bitable-bootstrap --preview --owner "Your Name"
npm run feishu -- bitable-bootstrap --confirm --owner "Your Name"
```

真实创建必须加 `--confirm`。命令会使用用户身份创建 Base / 表，并把 `FEISHU_BITABLE_APP_TOKEN`、`FEISHU_BITABLE_TABLE_ID` 写入本地 `.env`。

可以先用 `bitable_v1_app_create` 创建一个新的 Base。
如果创建后的 Base 需要当前用户直接打开，使用 `useUAT: true`。

### 创建表结构

`bitable_v1_appTable_create` 适合先搭一个最小可用表，再逐步扩字段。
字段配置里最常见的是 `Text`、`SingleSelect`、`Date` 这些基础类型。

### 搜索记录

`bitable_v1_appTableRecord_search` 的 `filter.value` 需要传数组，这一点容易写错。
如果搜索条件不生效，先检查这里。

### 创建记录

`bitable_v1_appTableRecord_create` 适合把项目状态、发布记录、风险项这类结构化信息写入 Base。

### 当前推荐模板

当前最适合先做的 4 张表：

- Project status
- Release records
- Risk tracker
- Case study intake

建议优先落地这两张：

- `Project Status`：最适合跟踪当前工作、责任人和下一步
- `Release Records`：最适合沉淀版本、验证结果和发布证据

### 当前边界

- Project Status 记录可以直接使用 `bitable_v1_appTableRecord_create`
- 其他尚未封装的 Bitable endpoint 继续使用 `feishu_openapi_request`
- 当前阶段交付的是项目运营模板和接入范式，不是完整的 Base ORM 或通用同步框架
