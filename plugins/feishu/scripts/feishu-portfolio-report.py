#!/usr/bin/env python3
import argparse
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time

from feishu_http_mcp import client


VALID_MODES = ("daily", "weekly", "custom")
VALID_STATUSES = ("Todo", "In Progress", "Blocked", "Done")


def build_parser():
    parser = argparse.ArgumentParser(
        description="Generate a Git-aware multi-project Codex portfolio report and optionally publish it to Feishu."
    )
    parser.add_argument("--preview", action="store_true", help="Preview only; this is the default.")
    parser.add_argument("--dry-run-json", action="store_true", help="Print structured output without writes.")
    parser.add_argument(
        "--projects-file",
        default=os.environ.get("FEISHU_PROJECTS_FILE") or "projects.json",
        help="JSON project registry. Defaults to FEISHU_PROJECTS_FILE or ./projects.json.",
    )
    parser.add_argument("--mode", choices=VALID_MODES, default="weekly")
    parser.add_argument("--since", help="Git-compatible date; required for custom mode.")
    parser.add_argument("--max-projects", type=int, default=20)
    parser.add_argument("--changed-only", action="store_true", help="Only include projects with commits or dirty state.")
    parser.add_argument("--include-paths", action="store_true", help="Include local workspace paths in local preview output.")
    parser.add_argument("--title")
    parser.add_argument("--write-doc", action="store_true")
    parser.add_argument("--bitable", action="store_true")
    parser.add_argument("--send", action="store_true")
    parser.add_argument("--confirm", action="store_true")
    return parser


def validate_options(options):
    problems = []
    projects_file = pathlib.Path(options.projects_file).expanduser()
    if not projects_file.is_file():
        problems.append(f"Projects file does not exist: {projects_file}")
    if options.mode == "custom" and not (options.since or "").strip():
        problems.append("--since is required when --mode custom is used.")
    if not 1 <= options.max_projects <= 50:
        problems.append("--max-projects must be between 1 and 50.")
    if options.bitable:
        for name in ("FEISHU_BITABLE_APP_TOKEN", "FEISHU_BITABLE_TABLE_ID"):
            if not os.environ.get(name, "").strip():
                problems.append(f"{name} is required with --bitable.")
    if options.send:
        for name in ("FEISHU_APP_ID", "FEISHU_APP_SECRET", "FEISHU_DEFAULT_RECEIVE_ID"):
            if not os.environ.get(name, "").strip():
                problems.append(f"{name} is required with --send.")
    if (options.write_doc or options.bitable) and not os.environ.get("FEISHU_USER_ACCESS_TOKEN", "").strip():
        problems.append("FEISHU_USER_ACCESS_TOKEN is required for Docx and Bitable writes.")
    return problems


def run_command(args, cwd, *, input_text=None, timeout=60, allow_failure=False):
    completed = subprocess.run(
        args,
        cwd=str(cwd),
        input=input_text,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0 and not allow_failure:
        message = completed.stderr.strip() or completed.stdout.strip() or f"exit code {completed.returncode}"
        raise RuntimeError(f"Command failed ({' '.join(args)}): {message}")
    return completed


def git_since(options):
    if options.mode == "daily":
        return "24 hours ago"
    if options.mode == "weekly":
        return "7 days ago"
    return options.since.strip()


def load_registry(path):
    registry_path = pathlib.Path(path).expanduser()
    try:
        payload = json.loads(registry_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Projects file is not valid JSON: {exc}") from exc
    projects = payload.get("projects")
    if not isinstance(projects, list):
        raise RuntimeError("Projects file must contain a projects array.")
    normalized = []
    for index, item in enumerate(projects, start=1):
        if not isinstance(item, dict):
            raise RuntimeError(f"Project #{index} must be an object.")
        if item.get("enabled", True) is False:
            continue
        name = str(item.get("name") or "").strip()
        workspace = str(item.get("workspace") or "").strip()
        if not name:
            raise RuntimeError(f"Project #{index} is missing name.")
        if not workspace:
            raise RuntimeError(f"Project {name} is missing workspace.")
        normalized.append(
            {
                "name": name,
                "workspace": str(pathlib.Path(workspace).expanduser()),
                "owner": str(item.get("owner") or "").strip(),
                "notes": str(item.get("notes") or "").strip(),
            }
        )
    if not normalized:
        raise RuntimeError("Projects file has no enabled projects.")
    return normalized


def collect_project_git(project, options):
    workspace = pathlib.Path(project["workspace"]).expanduser().resolve()
    if not workspace.is_dir():
        return {
            "name": project["name"],
            "owner": project["owner"],
            "notes": project["notes"],
            "workspace": str(workspace),
            "available": False,
            "error": f"Workspace is not a directory: {workspace}",
        }
    root_check = run_command(["git", "rev-parse", "--show-toplevel"], workspace, allow_failure=True)
    if root_check.returncode != 0:
        return {
            "name": project["name"],
            "owner": project["owner"],
            "notes": project["notes"],
            "workspace": str(workspace),
            "available": False,
            "error": "Workspace is not a Git repository.",
        }
    root = pathlib.Path(root_check.stdout.strip()).resolve()
    branch = run_command(["git", "branch", "--show-current"], root, allow_failure=True).stdout.strip() or "detached"
    status = run_command(["git", "status", "--short"], root).stdout.strip()
    diff_stat = run_command(["git", "diff", "--stat"], root).stdout.strip()
    log = run_command(
        [
            "git",
            "log",
            f"--since={git_since(options)}",
            "--date=short",
            "--pretty=format:%h%x09%ad%x09%s",
            "--max-count=30",
        ],
        root,
        allow_failure=True,
    ).stdout.strip()
    head = run_command(["git", "rev-parse", "--short", "HEAD"], root, allow_failure=True).stdout.strip()
    return {
        "name": project["name"],
        "owner": project["owner"],
        "notes": project["notes"],
        "workspace": str(root),
        "available": True,
        "branch": branch,
        "head": head or "unborn",
        "since": git_since(options),
        "commits": log.splitlines() if log else [],
        "working_tree": status.splitlines() if status else [],
        "diff_stat": diff_stat.splitlines() if diff_stat else [],
    }


def collect_projects(projects, options):
    selected = projects[: options.max_projects]
    contexts = [collect_project_git(project, options) for project in selected]
    if options.changed_only:
        contexts = [
            item
            for item in contexts
            if (not item.get("available")) or item.get("commits") or item.get("working_tree") or item.get("diff_stat")
        ]
    if not contexts:
        raise RuntimeError("No projects to report after applying filters.")
    return contexts


def report_schema():
    return {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "summary": {"type": "string"},
            "overall_status": {"type": "string", "enum": list(VALID_STATUSES)},
            "projects": {
                "type": "array",
                "maxItems": 50,
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "status": {"type": "string", "enum": list(VALID_STATUSES)},
                        "summary": {"type": "string"},
                        "completed": {"type": "array", "maxItems": 10, "items": {"type": "string"}},
                        "in_progress": {"type": "array", "maxItems": 10, "items": {"type": "string"}},
                        "risks": {"type": "array", "maxItems": 10, "items": {"type": "string"}},
                        "next_steps": {"type": "array", "maxItems": 10, "items": {"type": "string"}},
                    },
                    "required": [
                        "name",
                        "status",
                        "summary",
                        "completed",
                        "in_progress",
                        "risks",
                        "next_steps",
                    ],
                    "additionalProperties": False,
                },
            },
            "portfolio_next_steps": {"type": "array", "maxItems": 10, "items": {"type": "string"}},
        },
        "required": ["title", "summary", "overall_status", "projects", "portfolio_next_steps"],
        "additionalProperties": False,
    }


def validate_report(report):
    required = ("title", "summary", "overall_status", "projects", "portfolio_next_steps")
    missing = [key for key in required if key not in report]
    if missing:
        raise RuntimeError(f"Codex portfolio report is missing fields: {', '.join(missing)}")
    if report["overall_status"] not in VALID_STATUSES:
        raise RuntimeError(f"Codex portfolio report has invalid overall_status: {report['overall_status']}")
    if not isinstance(report["projects"], list):
        raise RuntimeError("Codex portfolio report projects must be an array.")
    for project in report["projects"]:
        if not isinstance(project, dict):
            raise RuntimeError("Codex portfolio report project item must be an object.")
        for key in ("name", "status", "summary", "completed", "in_progress", "risks", "next_steps"):
            if key not in project:
                raise RuntimeError(f"Codex portfolio project is missing field: {key}")
        if project["status"] not in VALID_STATUSES:
            raise RuntimeError(f"Codex portfolio project has invalid status: {project['status']}")
        for key in ("completed", "in_progress", "risks", "next_steps"):
            if not isinstance(project[key], list) or not all(isinstance(item, str) for item in project[key]):
                raise RuntimeError(f"Codex portfolio project field must be a string array: {key}")
    if not isinstance(report["portfolio_next_steps"], list) or not all(
        isinstance(item, str) for item in report["portfolio_next_steps"]
    ):
        raise RuntimeError("Codex portfolio_next_steps must be a string array.")
    return report


def redact_context(contexts, include_paths):
    redacted = []
    for item in contexts:
        value = dict(item)
        if not include_paths:
            value.pop("workspace", None)
        redacted.append(value)
    return redacted


def generate_report(project_contexts, options):
    prompt = """Generate a concise Simplified Chinese portfolio report from the supplied Git context.
Use only supplied facts. Do not claim work was completed unless the evidence supports it.
Classify each project and the overall portfolio as Todo, In Progress, Blocked, or Done.
For projects without commits or working tree changes, say there was no visible Git activity in this period.
Keep items actionable and suitable for a Feishu private assistant update.
Return only the JSON object required by the output schema.

INPUT:
""" + json.dumps(
        {
            "period": {"mode": options.mode, "since": git_since(options)},
            "projects": redact_context(project_contexts, options.include_paths),
        },
        ensure_ascii=False,
    )

    first_workspace = next((item.get("workspace") for item in project_contexts if item.get("available")), os.getcwd())
    with tempfile.TemporaryDirectory(prefix="feishu-portfolio-") as temp_dir:
        schema_path = pathlib.Path(temp_dir) / "schema.json"
        output_path = pathlib.Path(temp_dir) / "portfolio-report.json"
        schema_path.write_text(json.dumps(report_schema(), ensure_ascii=False), encoding="utf-8")
        timeout = int(os.environ.get("FEISHU_REPORT_CODEX_TIMEOUT_SECONDS", "600"))
        result = run_command(
            [
                os.environ.get("FEISHU_CODEX_BIN", "codex"),
                "exec",
                "--ephemeral",
                "--sandbox",
                "read-only",
                "-C",
                first_workspace,
                "--output-schema",
                str(schema_path),
                "--output-last-message",
                str(output_path),
                "-",
            ],
            first_workspace,
            input_text=prompt,
            timeout=timeout,
        )
        if not output_path.exists():
            raise RuntimeError(result.stderr.strip() or "Codex did not produce a portfolio report output file.")
        try:
            report = json.loads(output_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Codex portfolio report is not valid JSON: {exc}") from exc

    report = validate_report(report)
    if options.title:
        report["title"] = options.title.strip()
    return report


def markdown_section(title, items):
    values = items or ["无"]
    return f"### {title}\n\n" + "\n".join(f"- {item}" for item in values)


def render_markdown(report):
    sections = [
        f"# {report['title']}",
        report["summary"],
        f"**Overall Status:** {report['overall_status']}",
    ]
    for project in report["projects"]:
        sections.extend(
            [
                f"## {project['name']} · {project['status']}",
                project["summary"],
                markdown_section("已完成", project["completed"]),
                markdown_section("进行中", project["in_progress"]),
                markdown_section("风险阻塞", project["risks"]),
                markdown_section("下一步", project["next_steps"]),
            ]
        )
    sections.append(markdown_section("组合下一步", report["portfolio_next_steps"]))
    return "\n\n".join(sections).strip() + "\n"


def text_elements(content):
    return [{"text_run": {"content": content}}]


def report_to_blocks(report):
    blocks = [
        {"block_type": 2, "text": {"elements": text_elements(report["summary"])}},
        {"block_type": 2, "text": {"elements": text_elements(f"Overall Status: {report['overall_status']}")}},
    ]
    for project in report["projects"]:
        blocks.append(
            {
                "block_type": 4,
                "heading2": {"elements": text_elements(f"{project['name']} · {project['status']}")},
            }
        )
        blocks.append({"block_type": 2, "text": {"elements": text_elements(project["summary"])}})
        for title, items in (
            ("已完成", project["completed"]),
            ("进行中", project["in_progress"]),
            ("风险阻塞", project["risks"]),
            ("下一步", project["next_steps"]),
        ):
            blocks.append({"block_type": 5, "heading3": {"elements": text_elements(title)}})
            for item in items or ["无"]:
                blocks.append({"block_type": 12, "bullet": {"elements": text_elements(item)}})
    blocks.append({"block_type": 4, "heading2": {"elements": text_elements("组合下一步")}})
    for item in report["portfolio_next_steps"] or ["无"]:
        blocks.append({"block_type": 12, "bullet": {"elements": text_elements(item)}})
    return blocks


def create_document(report):
    body = {"title": report["title"]}
    folder_token = os.environ.get("FEISHU_REPORT_FOLDER_TOKEN", "").strip()
    if folder_token:
        body["folder_token"] = folder_token
    created = client.request("POST", "/open-apis/docx/v1/documents", body=body, token_mode="user")
    document = (created.get("data") or {}).get("document") or {}
    document_id = document.get("document_id")
    if not document_id:
        raise RuntimeError("Feishu created no document_id.")
    blocks = report_to_blocks(report)
    for index in range(0, len(blocks), 50):
        client.request(
            "POST",
            f"/open-apis/docx/v1/documents/{document_id}/blocks/{document_id}/children",
            body={"children": blocks[index : index + 50]},
            token_mode="user",
        )
    meta = client.request(
        "POST",
        "/open-apis/drive/v1/metas/batch_query",
        body={"request_docs": [{"doc_token": document_id, "doc_type": "docx"}], "with_url": True},
        token_mode="user",
    )
    metas = (meta.get("data") or {}).get("metas") or []
    return {"document_id": document_id, "url": metas[0].get("url") if metas else ""}


def create_bitable_records(report, contexts):
    context_by_name = {item["name"]: item for item in contexts}
    records = []
    for project in report["projects"]:
        context = context_by_name.get(project["name"], {})
        fields = {
            "Project": project["name"],
            "Status": project["status"],
            "Owner": context.get("owner") or os.environ.get("FEISHU_PROJECT_OWNER", "").strip() or "Unknown",
            "Next Step": (project["next_steps"] or ["无"])[0],
            "Updated At": int(time.time() * 1000),
        }
        payload = client.request(
            "POST",
            "/open-apis/bitable/v1/apps/{}/tables/{}/records".format(
                os.environ["FEISHU_BITABLE_APP_TOKEN"].strip(),
                os.environ["FEISHU_BITABLE_TABLE_ID"].strip(),
            ),
            body={"fields": fields},
            token_mode="user",
        )
        record = (payload.get("data") or {}).get("record") or {}
        records.append({"project": project["name"], "record_id": record.get("record_id", "")})
    return records


def build_message(report, document):
    lines = [report["title"], "", report["summary"], "", f"整体状态：{report['overall_status']}"]
    for project in report["projects"][:8]:
        next_step = (project["next_steps"] or ["无"])[0]
        lines.append(f"- {project['name']}：{project['status']}｜{next_step}")
    if len(report["projects"]) > 8:
        lines.append(f"- 另有 {len(report['projects']) - 8} 个项目见完整文档")
    if document and document.get("url"):
        lines.extend(["", f"完整文档：{document['url']}"])
    return "\n".join(lines)


def send_message(report, document):
    receive_id = os.environ["FEISHU_DEFAULT_RECEIVE_ID"].strip()
    receive_id_type = os.environ.get("FEISHU_DEFAULT_RECEIVE_ID_TYPE", "open_id").strip()
    if receive_id_type not in ("open_id", "chat_id"):
        raise RuntimeError("FEISHU_DEFAULT_RECEIVE_ID_TYPE must be open_id or chat_id.")
    payload = client.request(
        "POST",
        "/open-apis/im/v1/messages",
        query={"receive_id_type": receive_id_type},
        body={
            "receive_id": receive_id,
            "msg_type": "text",
            "content": json.dumps({"text": build_message(report, document)}, ensure_ascii=False),
        },
        token_mode="tenant",
    )
    return {"message_id": ((payload.get("data") or {}).get("message_id") or "")}


def action_plan(options):
    return {
        "write_doc": options.write_doc,
        "write_bitable": options.bitable,
        "send_message": options.send,
        "confirmed": bool(options.confirm and not options.preview and not options.dry_run_json),
    }


def execute_writes(options, report, contexts):
    completed = {}
    try:
        if options.write_doc:
            completed["document"] = create_document(report)
        if options.bitable:
            completed["bitable"] = create_bitable_records(report, contexts)
        if options.send:
            completed["message"] = send_message(report, completed.get("document"))
    except Exception as exc:
        print(json.dumps({"ok": False, "completed": completed, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise
    return completed


def main(argv=None):
    options = build_parser().parse_args(argv)
    problems = validate_options(options)
    if problems:
        for problem in problems:
            print(f"error: {problem}", file=sys.stderr)
        return 2

    try:
        projects = load_registry(options.projects_file)
        contexts = collect_projects(projects, options)
        report = generate_report(contexts, options)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    plan = action_plan(options)
    if options.dry_run_json:
        print(
            json.dumps(
                {
                    "report": report,
                    "projects": redact_context(contexts, options.include_paths),
                    "actions": plan,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    print(render_markdown(report))
    if not plan["confirmed"]:
        requested = [key for key, enabled in plan.items() if key != "confirmed" and enabled]
        if requested:
            print("Preview only. Add --confirm without --preview to perform: " + ", ".join(requested))
        return 0

    try:
        completed = execute_writes(options, report, contexts)
    except Exception:
        return 1
    print(json.dumps({"ok": True, "completed": completed}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
