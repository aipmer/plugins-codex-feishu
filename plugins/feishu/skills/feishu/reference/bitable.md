# Bitable

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

- If the MCP runtime does not yet expose a stable first-class Bitable wrapper for your exact endpoint, use `feishu_openapi_request` as the transition path.
- The current stage focuses on reusable project operation templates, not a full Base abstraction layer.

## 中文说明

### 创建 Base

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

- 如果当前 MCP 还没有覆盖你要调用的稳定 Bitable endpoint，先用 `feishu_openapi_request`
- 当前阶段交付的是项目运营模板和接入范式，不是完整的 Base ORM 或通用同步框架
