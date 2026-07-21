#!/usr/bin/env python3
import argparse
import json
import os
import pathlib
import sys

from feishu_http_mcp import FeishuError, client


STATUS_OPTIONS = ("Todo", "In Progress", "Blocked", "Done")
PROJECT_STATUS_FIELDS = (
    {"field_name": "Project", "type": 1},
    {
        "field_name": "Status",
        "type": 3,
        "property": {"options": [{"name": name} for name in STATUS_OPTIONS]},
    },
    {"field_name": "Owner", "type": 1},
    {"field_name": "Next Step", "type": 1},
    {"field_name": "Updated At", "type": 5},
)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Create a Feishu Bitable Project Status table for report --bitable."
    )
    parser.add_argument("--preview", action="store_true", help="Preview only; this is the default.")
    parser.add_argument("--confirm", action="store_true", help="Required for real Feishu writes.")
    parser.add_argument("--dry-run-json", action="store_true", help="Print the planned Base/table/env config.")
    parser.add_argument("--app-name", default=os.environ.get("FEISHU_BITABLE_APP_NAME") or "Codex Project Operations")
    parser.add_argument("--table-name", default=os.environ.get("FEISHU_BITABLE_TABLE_NAME") or "Project Status")
    parser.add_argument("--project-name", default=os.environ.get("FEISHU_PROJECT_NAME") or "Feishu for Codex")
    parser.add_argument("--owner", default=os.environ.get("FEISHU_PROJECT_OWNER") or "")
    parser.add_argument("--app-token", default=os.environ.get("FEISHU_BITABLE_APP_TOKEN") or "")
    parser.add_argument("--env-file", default=os.environ.get("FEISHU_ENV_FILE") or ".env")
    parser.add_argument("--no-write-env", action="store_true", help="Do not write FEISHU_BITABLE_* values to .env.")
    return parser


def quote_env(value):
    value = str(value)
    if not value or any(ch.isspace() for ch in value) or '"' in value:
        return json.dumps(value, ensure_ascii=False)
    return value


def upsert_env(env_file, values):
    env_path = pathlib.Path(env_file)
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()
    else:
        lines = []

    for name, value in values.items():
        if value is None or value == "":
            continue
        line = f"{name}={quote_env(value)}"
        for index, existing in enumerate(lines):
            if existing.startswith(name + "="):
                lines[index] = line
                break
        else:
            lines.append(line)

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate(options):
    problems = []
    if not os.environ.get("FEISHU_USER_ACCESS_TOKEN", "").strip():
        problems.append("FEISHU_USER_ACCESS_TOKEN is required. Run `npm run feishu -- auth` first.")
    if not os.environ.get("FEISHU_USER_REFRESH_TOKEN", "").strip():
        problems.append("FEISHU_USER_REFRESH_TOKEN is recommended for long-running Bitable workflows.")
    if not options.owner.strip():
        problems.append("--owner or FEISHU_PROJECT_OWNER is required.")
    if options.confirm and options.preview:
        problems.append("--preview and --confirm cannot be used together.")
    return problems


def plan(options):
    return {
        "app_name": options.app_name,
        "table_name": options.table_name,
        "project_name": options.project_name,
        "owner": options.owner,
        "reuse_app_token": bool(options.app_token.strip()),
        "write_env": not options.no_write_env,
        "fields": [
            {
                "field_name": field["field_name"],
                "type": field["type"],
                "options": [item["name"] for item in field.get("property", {}).get("options", [])],
            }
            for field in PROJECT_STATUS_FIELDS
        ],
        "env_keys": [
            "FEISHU_PROJECT_NAME",
            "FEISHU_PROJECT_OWNER",
            "FEISHU_BITABLE_APP_TOKEN",
            "FEISHU_BITABLE_TABLE_ID",
        ],
    }


def create_app(options):
    if options.app_token.strip():
        return options.app_token.strip(), {"reused": True}
    payload = client.request(
        "POST",
        "/open-apis/bitable/v1/apps",
        body={"name": options.app_name, "time_zone": "Asia/Shanghai"},
        token_mode="user",
    )
    data = payload.get("data") or {}
    app = data.get("app") or data
    app_token = app.get("app_token")
    if not app_token:
        raise RuntimeError("Feishu created no Bitable app_token.")
    return app_token, {"reused": False}


def create_table(app_token, options):
    payload = client.request(
        "POST",
        f"/open-apis/bitable/v1/apps/{app_token}/tables",
        body={"table": {"name": options.table_name}},
        token_mode="user",
    )
    data = payload.get("data") or {}
    table = data.get("table") or data
    table_id = table.get("table_id") or table.get("id")
    if not table_id:
        raise RuntimeError("Feishu created no Bitable table_id.")
    return table_id


def create_fields(app_token, table_id):
    created = []
    for field in PROJECT_STATUS_FIELDS:
        payload = client.request(
            "POST",
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
            body=field,
            token_mode="user",
        )
        data = payload.get("data") or {}
        created_field = data.get("field") or data
        created.append(
            {
                "field_name": created_field.get("field_name") or field["field_name"],
                "field_id": created_field.get("field_id", ""),
                "ui_type": created_field.get("ui_type", ""),
                "type": created_field.get("type", field["type"]),
            }
        )
    return created


def execute(options):
    app_token, app_meta = create_app(options)
    table_id = create_table(app_token, options)
    fields = create_fields(app_token, table_id)
    env_values = {
        "FEISHU_PROJECT_NAME": options.project_name,
        "FEISHU_PROJECT_OWNER": options.owner,
        "FEISHU_BITABLE_APP_TOKEN": app_token,
        "FEISHU_BITABLE_TABLE_ID": table_id,
    }
    if not options.no_write_env:
        upsert_env(options.env_file, env_values)
    return {
        "ok": True,
        "app": {"app_token": app_token, **app_meta},
        "table": {"table_id": table_id, "name": options.table_name},
        "fields": fields,
        "env_written": not options.no_write_env,
    }


def main(argv=None):
    options = build_parser().parse_args(argv)
    problems = validate(options)
    if problems:
        for problem in problems:
            print(f"error: {problem}", file=sys.stderr)
        return 2

    planned = plan(options)
    if options.dry_run_json or options.preview or not options.confirm:
        print(json.dumps({"ok": True, "preview": True, "plan": planned}, ensure_ascii=False, indent=2))
        return 0

    try:
        result = execute(options)
    except FeishuError as exc:
        payload = getattr(exc, "payload", None)
        print(json.dumps({"ok": False, "error": str(exc), "payload": payload}, ensure_ascii=False), file=sys.stderr)
        return 1
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
