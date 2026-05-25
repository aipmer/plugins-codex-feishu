#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN_DIR="${REPO_ROOT}/plugins/feishu"

fail() {
  echo "fail: $*" >&2
  exit 1
}

ok() {
  echo "ok: $*"
}

require_file() {
  local path="$1"
  [[ -f "${path}" ]] || fail "missing file: ${path}"
  ok "found ${path#${REPO_ROOT}/}"
}

require_executable() {
  local path="$1"
  [[ -x "${path}" ]] || fail "not executable: ${path}"
  ok "executable ${path#${REPO_ROOT}/}"
}

require_file "${PLUGIN_DIR}/.codex-plugin/plugin.json"
require_file "${PLUGIN_DIR}/.mcp.json"
require_file "${PLUGIN_DIR}/skills/feishu/SKILL.md"
require_file "${PLUGIN_DIR}/scripts/feishu_http_mcp.py"
require_file "${PLUGIN_DIR}/scripts/feishu-long-connection-bot.js"
require_file "${PLUGIN_DIR}/scripts/feishu-project-update.js"
require_file "${PLUGIN_DIR}/scripts/feishu_webhook_server.py"
require_file "${PLUGIN_DIR}/scripts/test-feishu-webhook.py"
require_file "${PLUGIN_DIR}/skills/feishu/examples/quickstart-message-bot.md"
require_file "${PLUGIN_DIR}/skills/feishu/examples/docs-wiki-to-doc.md"
require_file "${PLUGIN_DIR}/skills/feishu/examples/bitable-project-templates.md"
require_file "${PLUGIN_DIR}/testdata/webhook/url_verification.json"
require_file "${PLUGIN_DIR}/testdata/webhook/message_receive_v1.json"
require_file "${REPO_ROOT}/docs/platform-roadmap.md"
require_file "${REPO_ROOT}/case-studies/2026-05-25-private-assistant-push.md"
require_file "${REPO_ROOT}/case-studies/2026-05-25-message-bot-quickstart.md"
require_file "${REPO_ROOT}/case-studies/2026-05-25-docs-wiki-writeback.md"
require_file "${REPO_ROOT}/.env.example"
require_file "${REPO_ROOT}/package.json"
require_file "${REPO_ROOT}/scripts/check-sensitive-values.sh"
require_executable "${PLUGIN_DIR}/scripts/generate-feishu-auth-url.sh"
require_executable "${PLUGIN_DIR}/scripts/exchange-feishu-code.sh"
require_executable "${PLUGIN_DIR}/scripts/doctor-feishu-auth.sh"
require_executable "${PLUGIN_DIR}/scripts/feishu-long-connection-bot.js"
require_executable "${PLUGIN_DIR}/scripts/feishu-project-update.js"
require_executable "${PLUGIN_DIR}/scripts/feishu_http_mcp.py"
require_executable "${PLUGIN_DIR}/scripts/feishu_webhook_server.py"
require_executable "${PLUGIN_DIR}/scripts/test-feishu-webhook.py"
require_executable "${REPO_ROOT}/scripts/check-sensitive-values.sh"

python3 - <<'PY' "${REPO_ROOT}"
import json
import pathlib
import subprocess
import sys

repo_root = pathlib.Path(sys.argv[1])
plugin_dir = repo_root / "plugins" / "feishu"

for relative in [
    "package.json",
    "plugins/feishu/.codex-plugin/plugin.json",
    "plugins/feishu/.mcp.json",
    ".agents/plugins/marketplace.json",
]:
    with (repo_root / relative).open("r", encoding="utf-8") as fh:
        json.load(fh)
    print(f"ok: valid JSON {relative}")

mcp_script = plugin_dir / "scripts" / "feishu_http_mcp.py"
init_request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "smoke-test", "version": "0.0.0"},
    },
}
tools_request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}

def frame(payload):
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return b"Content-Length: " + str(len(body)).encode("ascii") + b"\r\n\r\n" + body

proc = subprocess.run(
    ["python3", str(mcp_script)],
    input=frame(init_request) + frame(tools_request),
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    check=False,
    cwd=str(plugin_dir),
)

if proc.returncode != 0:
    raise SystemExit(proc.stderr.decode("utf-8", errors="replace") or proc.returncode)

output = proc.stdout
responses = []
while output:
    header, _, rest = output.partition(b"\r\n\r\n")
    if not rest:
        raise SystemExit("invalid MCP frame: missing header separator")
    headers = {}
    for line in header.decode("utf-8").split("\r\n"):
        key, value = line.split(":", 1)
        headers[key.lower()] = value.strip()
    length = int(headers["content-length"])
    body = rest[:length]
    output = rest[length:]
    responses.append(json.loads(body.decode("utf-8")))

if len(responses) != 2:
    raise SystemExit(f"expected 2 MCP responses, got {len(responses)}")

tools = responses[1].get("result", {}).get("tools", [])
tool_names = {tool.get("name") for tool in tools}
required_tools = {
    "im_v1_chat_list",
    "im_v1_message_list",
    "im_v1_message_create",
    "docx_builtin_search",
    "wiki_v1_node_search",
    "feishu_openapi_request",
}
missing = sorted(required_tools - tool_names)
if missing:
    raise SystemExit(f"missing MCP tools: {', '.join(missing)}")

print(f"ok: MCP initialize and tools/list returned {len(tools)} tools")

webhook_script = plugin_dir / "scripts" / "feishu_webhook_server.py"
webhook_check = subprocess.run(
    ["python3", str(webhook_script), "--self-test"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    check=False,
)
if webhook_check.returncode != 0:
    raise SystemExit(webhook_check.stderr or webhook_check.stdout)
print(webhook_check.stdout.strip())

webhook_fixture_check = subprocess.run(
    ["python3", str(plugin_dir / "scripts" / "test-feishu-webhook.py")],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    check=False,
)
if webhook_fixture_check.returncode != 0:
    raise SystemExit(webhook_fixture_check.stderr or webhook_fixture_check.stdout)
print(webhook_fixture_check.stdout.strip())

long_connection_check = subprocess.run(
    ["node", "-c", str(plugin_dir / "scripts" / "feishu-long-connection-bot.js")],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    check=False,
)
if long_connection_check.returncode != 0:
    raise SystemExit(long_connection_check.stderr or long_connection_check.stdout)
print("ok: long connection bot syntax check passed")

project_update_check = subprocess.run(
    ["node", "-c", str(plugin_dir / "scripts" / "feishu-project-update.js")],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    check=False,
)
if project_update_check.returncode != 0:
    raise SystemExit(project_update_check.stderr or project_update_check.stdout)
print("ok: project update push syntax check passed")
PY

"${REPO_ROOT}/scripts/check-sensitive-values.sh"

echo "Smoke test passed."
