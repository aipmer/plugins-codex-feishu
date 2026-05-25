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

Recommended v0.3 tables:

- Project status
- Release records
- Risk tracker
- Case study intake

See `examples/bitable-project-templates.md` for fields and record examples.
