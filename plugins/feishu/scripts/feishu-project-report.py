#!/usr/bin/env python3
import argparse
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time

from feishu_http_mcp import FeishuError, client


VALID_MODES = ("daily", "weekly", "custom")
VALID_STATUSES = ("Todo", "In Progress", "Blocked", "Done")
MAX_CONTEXT_CHARS = 30000


def build_parser():
    parser = argparse.ArgumentParser(
        description="Generate a Git-aware Codex project report and optionally write it to Feishu."
    )
    parser.add_argument("--preview", action="store_true", help="Preview only; this is the default.")
    parser.add_argument("--dry-run-json", action="store_true", help="Print structured output without writes.")
    parser.add_argument("--mode", choices=VALID_MODES, default="weekly")
    parser.add_argument("--since", help="Git-compatible date; required for custom mode.")
    parser.add_argument("--workspace", default=os.environ.get("FEISHU_DEFAULT_WORKSPACE") or os.getcwd())
    parser.add_argument("--query", action="append", default=[], help="Feishu Docs/Wiki keyword; repeatable.")
    parser.add_argument("--max-sources", type=int, default=3)
    parser.add_argument("--title")
    parser.add_argument("--write-doc", action="store_true")
    parser.add_argument("--bitable", action="store_true")
    parser.add_argument("--send", action="store_true")
    parser.add_argument("--confirm", action="store_true")
    return parser


def validate_options(options):
    problems = []
    workspace = pathlib.Path(options.workspace).expanduser().resolve()
    if not workspace.is_dir():
        problems.append(f"Workspace is not a directory: {workspace}")
    if options.mode == "custom" and not (options.since or "").strip():
        problems.append("--since is required when --mode custom is used.")
    if not 1 <= options.max_sources <= 5:
        problems.append("--max-sources must be between 1 and 5.")
    if options.bitable:
        for name in ("FEISHU_BITABLE_APP_TOKEN", "FEISHU_BITABLE_TABLE_ID", "FEISHU_PROJECT_OWNER"):
            if not os.environ.get(name, "").strip():
                problems.append(f"{name} is required with --bitable.")
    if options.send:
        for name in ("FEISHU_APP_ID", "FEISHU_APP_SECRET", "FEISHU_DEFAULT_RECEIVE_ID"):
            if not os.environ.get(name, "").strip():
                problems.append(f"{name} is required with --send.")
    if (options.query or options.write_doc or options.bitable) and not os.environ.get(
        "FEISHU_USER_ACCESS_TOKEN", ""
    ).strip():
        problems.append("FEISHU_USER_ACCESS_TOKEN is required for knowledge lookup and user-owned writes.")
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


def collect_git_context(workspace, options):
    root_check = run_command(
        ["git", "rev-parse", "--show-toplevel"], workspace, allow_failure=True
    )
    if root_check.returncode != 0:
        raise RuntimeError(f"Workspace is not a Git repository: {workspace}")
    root = pathlib.Path(root_check.stdout.strip()).resolve()
    branch = run_command(
        ["git", "branch", "--show-current"], root, allow_failure=True
    ).stdout.strip() or "detached"
    status = run_command(["git", "status", "--short"], root).stdout.strip()
    diff_stat = run_command(["git", "diff", "--stat"], root).stdout.strip()
    log = run_command(
        [
            "git",
            "log",
            f"--since={git_since(options)}",
            "--date=short",
            "--pretty=format:%h%x09%ad%x09%s",
            "--max-count=50",
        ],
        root,
        allow_failure=True,
    ).stdout.strip()
    head = run_command(
        ["git", "rev-parse", "--short", "HEAD"], root, allow_failure=True
    ).stdout.strip()
    return {
        "workspace": str(root),
        "project": os.environ.get("FEISHU_PROJECT_NAME", "").strip() or root.name,
        "branch": branch,
        "head": head or "unborn",
        "since": git_since(options),
        "commits": log.splitlines() if log else [],
        "working_tree": status.splitlines() if status else [],
        "diff_stat": diff_stat.splitlines() if diff_stat else [],
    }


def first_list(payload, keys):
    data = payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(data, dict):
        return []
    for key in keys:
        value = data.get(key)
        if isinstance(value, list):
            return value
    return []


def value_from(item, *keys):
    if not isinstance(item, dict):
        return ""
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def normalize_doc_candidate(item, query):
    token = value_from(item, "docs_token", "document_id", "doc_token", "token", "obj_token")
    if not token:
        return None
    return {
        "query": query,
        "kind": "docx",
        "token": token,
        "title": value_from(item, "title", "name") or token,
    }


def normalize_wiki_candidate(item, query):
    node = item.get("node") if isinstance(item, dict) and isinstance(item.get("node"), dict) else item
    token = value_from(node, "obj_token")
    obj_type = value_from(node, "obj_type")
    if token and obj_type == "docx":
        return {
            "query": query,
            "kind": "wiki",
            "token": token,
            "title": value_from(node, "title", "name") or token,
        }
    node_token = value_from(node, "node_token", "wiki_token", "token")
    if not node_token:
        return None
    resolved = client.request(
        "GET",
        "/open-apis/wiki/v2/spaces/get_node",
        query={"token": node_token},
        token_mode="user",
    )
    resolved_node = (resolved.get("data") or {}).get("node") or resolved.get("data") or {}
    resolved_token = value_from(resolved_node, "obj_token")
    if value_from(resolved_node, "obj_type") != "docx" or not resolved_token:
        return None
    return {
        "query": query,
        "kind": "wiki",
        "token": resolved_token,
        "title": value_from(resolved_node, "title") or value_from(node, "title") or resolved_token,
    }


def read_doc_source(candidate):
    payload = client.request(
        "GET",
        f"/open-apis/docx/v1/documents/{candidate['token']}/raw_content",
        token_mode="user",
    )
    data = payload.get("data") or {}
    content = value_from(data, "content")
    if not content:
        return None
    return {**candidate, "content": content, "truncated": False}


def collect_feishu_sources(queries, max_sources, max_chars=MAX_CONTEXT_CHARS):
    sources = []
    remaining = max_chars
    seen = set()

    def append_candidates(candidates):
        nonlocal remaining
        for candidate in candidates:
            if len(sources) >= max_sources or remaining <= 0:
                break
            if candidate["token"] in seen:
                continue
            seen.add(candidate["token"])
            try:
                source = read_doc_source(candidate)
            except FeishuError:
                continue
            if not source:
                continue
            if len(source["content"]) > remaining:
                source["content"] = source["content"][:remaining]
                source["truncated"] = True
            remaining -= len(source["content"])
            sources.append(source)

    for raw_query in queries:
        query = raw_query.strip()
        if not query or len(sources) >= max_sources:
            continue
        docs = client.request(
            "POST",
            "/open-apis/suite/docs-api/search/object",
            body={"search_key": query, "count": max_sources},
            token_mode="user",
        )
        candidates = [
            normalize_doc_candidate(item, query)
            for item in first_list(docs, ("docs_entities", "items", "docs"))
        ]
        candidates = [item for item in candidates if item]
        source_count = len(sources)
        append_candidates(candidates)
        if len(sources) == source_count and len(sources) < max_sources and remaining > 0:
            wiki = client.request(
                "POST",
                "/open-apis/wiki/v2/nodes/search",
                body={"query": query, "page_size": max_sources},
                token_mode="user",
            )
            candidates = [
                normalize_wiki_candidate(item, query)
                for item in first_list(wiki, ("items", "nodes"))
            ]
            candidates = [item for item in candidates if item]
            append_candidates(candidates)
    return sources


def report_schema():
    properties = {
        "title": {"type": "string"},
        "summary": {"type": "string"},
        "status": {"type": "string", "enum": list(VALID_STATUSES)},
        "completed": {"type": "array", "maxItems": 20, "items": {"type": "string", "maxLength": 2000}},
        "in_progress": {"type": "array", "maxItems": 20, "items": {"type": "string", "maxLength": 2000}},
        "risks": {"type": "array", "maxItems": 20, "items": {"type": "string", "maxLength": 2000}},
        "next_steps": {"type": "array", "maxItems": 20, "items": {"type": "string", "maxLength": 2000}},
        "sources": {"type": "array", "maxItems": 5, "items": {"type": "string", "maxLength": 500}},
    }
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


def validate_report(report):
    required = ("title", "summary", "status", "completed", "in_progress", "risks", "next_steps", "sources")
    missing = [key for key in required if key not in report]
    if missing:
        raise RuntimeError(f"Codex report is missing fields: {', '.join(missing)}")
    if report["status"] not in VALID_STATUSES:
        raise RuntimeError(f"Codex report has invalid status: {report['status']}")
    for key in ("completed", "in_progress", "risks", "next_steps", "sources"):
        if not isinstance(report[key], list) or not all(isinstance(item, str) for item in report[key]):
            raise RuntimeError(f"Codex report field must be a string array: {key}")
    if not isinstance(report["title"], str) or not isinstance(report["summary"], str):
        raise RuntimeError("Codex report title and summary must be strings.")
    return report


def generate_report(git_context, sources, options):
    source_context = [
        {
            "title": item["title"],
            "token": item["token"],
            "query": item["query"],
            "truncated": item["truncated"],
            "content": item["content"],
        }
        for item in sources
    ]
    prompt = """Generate a concise Simplified Chinese project report from the supplied Git and Feishu context.
Use only supplied facts. Do not claim work was completed unless the evidence supports it.
Classify the overall status as Todo, In Progress, Blocked, or Done.
Keep each list item actionable and suitable for a Feishu project update.
Return only the JSON object required by the output schema.

INPUT:
""" + json.dumps({"git": git_context, "feishu_sources": source_context}, ensure_ascii=False)

    with tempfile.TemporaryDirectory(prefix="feishu-report-") as temp_dir:
        schema_path = pathlib.Path(temp_dir) / "schema.json"
        output_path = pathlib.Path(temp_dir) / "report.json"
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
                git_context["workspace"],
                "--output-schema",
                str(schema_path),
                "--output-last-message",
                str(output_path),
                "-",
            ],
            git_context["workspace"],
            input_text=prompt,
            timeout=timeout,
        )
        if not output_path.exists():
            raise RuntimeError(result.stderr.strip() or "Codex did not produce a report output file.")
        try:
            report = json.loads(output_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Codex report is not valid JSON: {exc}") from exc

    report = validate_report(report)
    if options.title:
        report["title"] = options.title.strip()
    report["sources"] = [item["title"] for item in sources]
    return report


def markdown_section(title, items):
    values = items or ["无"]
    return f"## {title}\n\n" + "\n".join(f"- {item}" for item in values)


def render_markdown(report, sources):
    sections = [
        f"# {report['title']}",
        report["summary"],
        f"**Status:** {report['status']}",
        markdown_section("已完成", report["completed"]),
        markdown_section("进行中", report["in_progress"]),
        markdown_section("风险阻塞", report["risks"]),
        markdown_section("下一步", report["next_steps"]),
    ]
    if sources:
        sections.append(markdown_section("参考来源", [item["title"] for item in sources]))
    return "\n\n".join(sections).strip() + "\n"


def text_elements(content):
    return [{"text_run": {"content": content}}]


def report_to_blocks(report, sources):
    blocks = [
        {"block_type": 2, "text": {"elements": text_elements(report["summary"])}},
        {"block_type": 2, "text": {"elements": text_elements(f"Status: {report['status']}")}},
    ]
    for title, items in (
        ("已完成", report["completed"]),
        ("进行中", report["in_progress"]),
        ("风险阻塞", report["risks"]),
        ("下一步", report["next_steps"]),
    ):
        blocks.append({"block_type": 4, "heading2": {"elements": text_elements(title)}})
        for item in items or ["无"]:
            blocks.append({"block_type": 12, "bullet": {"elements": text_elements(item)}})
    if sources:
        blocks.append({"block_type": 4, "heading2": {"elements": text_elements("参考来源")}})
        for source in sources:
            suffix = "（内容已截断）" if source["truncated"] else ""
            blocks.append(
                {"block_type": 12, "bullet": {"elements": text_elements(source["title"] + suffix)}}
            )
    return blocks


def create_document(report, sources):
    body = {"title": report["title"]}
    folder_token = os.environ.get("FEISHU_REPORT_FOLDER_TOKEN", "").strip()
    if folder_token:
        body["folder_token"] = folder_token
    created = client.request(
        "POST", "/open-apis/docx/v1/documents", body=body, token_mode="user"
    )
    document = (created.get("data") or {}).get("document") or {}
    document_id = document.get("document_id")
    if not document_id:
        raise RuntimeError("Feishu created no document_id.")
    blocks = report_to_blocks(report, sources)
    for index in range(0, len(blocks), 50):
        client.request(
            "POST",
            f"/open-apis/docx/v1/documents/{document_id}/blocks/{document_id}/children",
            body={"children": blocks[index:index + 50]},
            token_mode="user",
        )
    meta = client.request(
        "POST",
        "/open-apis/drive/v1/metas/batch_query",
        body={"request_docs": [{"doc_token": document_id, "doc_type": "docx"}], "with_url": True},
        token_mode="user",
    )
    metas = (meta.get("data") or {}).get("metas") or []
    return {
        "document_id": document_id,
        "url": metas[0].get("url") if metas else "",
    }


def create_bitable_record(report, git_context):
    fields = {
        "Project": git_context["project"],
        "Status": report["status"],
        "Owner": os.environ["FEISHU_PROJECT_OWNER"].strip(),
        "Next Step": (report["next_steps"] or ["无"])[0],
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
    return {"record_id": record.get("record_id", "")}


def build_message(report, document):
    lines = [report["title"], "", report["summary"], "", f"状态：{report['status']}"]
    if report["next_steps"]:
        lines.extend(["", "下一步：", *[f"- {item}" for item in report["next_steps"]]])
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


def execute_writes(options, report, sources, git_context):
    completed = {}
    try:
        if options.write_doc:
            completed["document"] = create_document(report, sources)
        if options.bitable:
            completed["bitable"] = create_bitable_record(report, git_context)
        if options.send:
            completed["message"] = send_message(report, completed.get("document"))
    except Exception as exc:
        print(
            json.dumps(
                {"ok": False, "completed": completed, "error": str(exc)},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        raise
    return completed


def main(argv=None):
    options = build_parser().parse_args(argv)
    problems = validate_options(options)
    if problems:
        for problem in problems:
            print(f"error: {problem}", file=sys.stderr)
        return 2

    workspace = pathlib.Path(options.workspace).expanduser().resolve()
    git_context = collect_git_context(workspace, options)
    sources = collect_feishu_sources(options.query, options.max_sources) if options.query else []
    report = generate_report(git_context, sources, options)
    markdown = render_markdown(report, sources)
    plan = action_plan(options)

    if options.dry_run_json:
        print(
            json.dumps(
                {
                    "report": report,
                    "git": git_context,
                    "sources": [
                        {key: item[key] for key in ("query", "kind", "token", "title", "truncated")}
                        for item in sources
                    ],
                    "actions": plan,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    print(markdown)
    if not plan["confirmed"]:
        requested = [key for key, enabled in plan.items() if key != "confirmed" and enabled]
        if requested:
            print("Preview only. Add --confirm without --preview to perform: " + ", ".join(requested))
        return 0

    completed = execute_writes(options, report, sources, git_context)
    print(json.dumps({"ok": True, "completed": completed}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FeishuError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
