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
require_file "${PLUGIN_DIR}/scripts/feishu-codex-runner.js"
require_file "${PLUGIN_DIR}/scripts/feishu-codex-echo.js"
require_file "${PLUGIN_DIR}/scripts/feishu-project-update.js"
require_file "${PLUGIN_DIR}/scripts/feishu-project-report.py"
require_file "${PLUGIN_DIR}/scripts/feishu-oauth-callback.py"
require_file "${PLUGIN_DIR}/scripts/feishu_webhook_server.py"
require_file "${PLUGIN_DIR}/scripts/test-feishu-webhook.py"
require_file "${PLUGIN_DIR}/skills/feishu/examples/quickstart-message-bot.md"
require_file "${PLUGIN_DIR}/skills/feishu/examples/docs-wiki-to-doc.md"
require_file "${PLUGIN_DIR}/skills/feishu/examples/bitable-project-templates.md"
require_file "${PLUGIN_DIR}/skills/feishu/examples/project-update-template.md"
require_file "${PLUGIN_DIR}/testdata/webhook/url_verification.json"
require_file "${PLUGIN_DIR}/testdata/webhook/message_receive_v1.json"
require_file "${REPO_ROOT}/docs/roadmap.md"
require_file "${REPO_ROOT}/docs/platform-roadmap.md"
require_file "${REPO_ROOT}/CHANGELOG.md"
require_file "${REPO_ROOT}/docs/dev_task.md"
require_file "${REPO_ROOT}/.env.example"
require_file "${REPO_ROOT}/package.json"
require_file "${REPO_ROOT}/scripts/feishu-codex.js"
require_file "${REPO_ROOT}/scripts/feishu-service.js"
require_file "${REPO_ROOT}/scripts/check-sensitive-values.sh"
require_executable "${PLUGIN_DIR}/scripts/generate-feishu-auth-url.sh"
require_executable "${PLUGIN_DIR}/scripts/exchange-feishu-code.sh"
require_executable "${PLUGIN_DIR}/scripts/doctor-feishu-auth.sh"
require_executable "${PLUGIN_DIR}/scripts/feishu-long-connection-bot.js"
require_executable "${PLUGIN_DIR}/scripts/feishu-codex-runner.js"
require_executable "${PLUGIN_DIR}/scripts/feishu-codex-echo.js"
require_executable "${PLUGIN_DIR}/scripts/feishu-project-update.js"
require_executable "${PLUGIN_DIR}/scripts/feishu-project-report.py"
require_executable "${PLUGIN_DIR}/scripts/feishu-oauth-callback.py"
require_executable "${PLUGIN_DIR}/scripts/feishu_http_mcp.py"
require_executable "${PLUGIN_DIR}/scripts/feishu_webhook_server.py"
require_executable "${PLUGIN_DIR}/scripts/test-feishu-webhook.py"
require_executable "${REPO_ROOT}/scripts/feishu-codex.js"
require_executable "${REPO_ROOT}/scripts/feishu-service.js"
require_executable "${REPO_ROOT}/scripts/check-sensitive-values.sh"

python3 - <<'PY' "${REPO_ROOT}"
import json
import pathlib
import re
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

readme = repo_root / "README.md"
readme_text = readme.read_text(encoding="utf-8")
for forbidden in [
    "README" + ".zh-CN.md",
    "docs/" + "releases/",
    "case-" + "studies/",
    "github.com/" + "hunkwu/book",
]:
    if forbidden in readme_text:
        raise SystemExit(f"README contains removed reference: {forbidden}")

readme_targets = [
    match.group(1).strip()
    for match in re.finditer(r"!?\[[^\]]*\]\(([^)]+)\)", readme_text)
]
readme_targets.extend(
    match.group(1).strip()
    for match in re.finditer(r"<img\b[^>]*\bsrc=[\"']([^\"']+)[\"']", readme_text)
)

for target in readme_targets:
    if not target or target.startswith(("#", "http://", "https://", "mailto:")):
        continue
    local_path = target.split("#", 1)[0]
    if local_path and not (repo_root / local_path).exists():
        raise SystemExit(f"README local link is missing: {target}")

print("ok: README local links and removed references check passed")

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
    "docx_v1_document_create",
    "docx_v1_documentBlockChildren_create",
    "drive_v1_meta_batchQuery",
    "bitable_v1_appTableRecord_create",
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

bot_logic_check = subprocess.run(
    [
        "node",
        "-e",
        """
const fs = require('fs');
const os = require('os');
const path = require('path');
const bot = require('./plugins/feishu/scripts/feishu-long-connection-bot.js');

const fixture = JSON.parse(fs.readFileSync('./plugins/feishu/testdata/webhook/message_receive_v1.json', 'utf8'));
const event = fixture.event;
const tmpRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'feishu-bot-state-'));
process.env.FEISHU_BOT_STATE_DIR = tmpRoot;
process.env.FEISHU_DEFAULT_WORKSPACE = process.cwd();

if (!bot.shouldHandleMessage(event)) {
  throw new Error('expected message fixture to be handled');
}
if (bot.parseTextContent(event.message.content) !== '请总结今天的项目进展') {
  throw new Error('unexpected parsed message text');
}

const sessionKey = bot.extractSessionKey(event);
if (sessionKey !== 'chat:oc_test_chat') {
  throw new Error(`unexpected session key: ${sessionKey}`);
}

const help = bot.parseCommand('/help');
if (!help || help.name != 'help') {
  throw new Error('expected /help command parsing');
}

const ids = bot.parseCommand('/ids');
if (!ids || ids.name != 'ids') {
  throw new Error('expected /ids command parsing');
}

const cd = bot.parseCommand('/cd ./plugins');
if (!cd || cd.name != 'cd' || cd.argText != './plugins') {
  throw new Error('expected /cd command parsing');
}

const saved = bot.saveSession({
  ...bot.createDefaultSession(sessionKey),
  workspace: process.cwd(),
  lastCommand: '/status',
}, tmpRoot);

const loaded = bot.loadSession(sessionKey, tmpRoot);
if (loaded.workspace !== process.cwd() || loaded.lastCommand !== '/status') {
  throw new Error('session persistence check failed');
}

const resolved = bot.resolveWorkspace('./plugins', process.cwd());
if (!resolved.endsWith(path.sep + 'plugins')) {
  throw new Error(`unexpected resolved workspace: ${resolved}`);
}

bot.resetSession(sessionKey, tmpRoot);
const reset = bot.loadSession(sessionKey, tmpRoot);
if (reset.lastCommand !== '' || reset.workspace !== process.cwd()) {
  throw new Error('session reset check failed');
}

const formattedStatus = bot.formatStatus(saved, false, {
  chatId: 'oc_test_chat',
  senderOpenId: 'ou_test_sender',
  runnerCommand: 'codex exec',
  serviceStatus: { loaded: true, launchctlState: 'running', pid: '12345' },
});
if (!formattedStatus.includes('Workspace:')) {
  throw new Error('status formatting check failed');
}
if (!formattedStatus.includes('Runner command: codex exec') || !formattedStatus.includes('Service loaded: yes')) {
  throw new Error(`status summary missing runner/service details: ${formattedStatus}`);
}

const deduped = bot.markMessageProcessed(saved, 'om_first');
if (!bot.hasProcessedMessage(deduped, 'om_first')) {
  throw new Error('message dedupe mark check failed');
}

const dedupedAgain = bot.markMessageProcessed(deduped, 'om_first');
if (dedupedAgain.recentMessageIds.length !== 1) {
  throw new Error('message dedupe should keep one recent message id');
}

const stale = bot.saveSession({
  ...loaded,
  running: true,
  status: 'running',
  currentPid: 12345,
}, tmpRoot);
const reconciled = bot.loadActiveSession(sessionKey, { hasRunning: () => false }, tmpRoot);
if (reconciled.running || reconciled.status !== 'failed' || reconciled.currentPid !== null) {
  throw new Error(`stale running session should reconcile to failed state: ${JSON.stringify({ stale, reconciled })}`);
}

console.log('ok: long connection bot local logic checks passed');
        """,
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    check=False,
    cwd=str(repo_root),
)
if bot_logic_check.returncode != 0:
    raise SystemExit(bot_logic_check.stderr or bot_logic_check.stdout)
print(bot_logic_check.stdout.strip())

runner_check = subprocess.run(
    ["node", "-c", str(plugin_dir / "scripts" / "feishu-codex-runner.js")],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    check=False,
)
if runner_check.returncode != 0:
    raise SystemExit(runner_check.stderr or runner_check.stdout)
print("ok: feishu codex runner syntax check passed")

runner_payload_check = subprocess.run(
    [
        "node",
        str(plugin_dir / "scripts" / "feishu-codex-runner.js"),
        "--print-payload",
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    check=False,
    cwd=str(repo_root),
    env={
        **__import__("os").environ,
        "FEISHU_MESSAGE_TEXT": "Summarize today's progress",
        "FEISHU_SESSION_KEY": "chat:test",
        "FEISHU_SESSION_WORKSPACE": str(repo_root),
        "FEISHU_RUNNER_COMMAND": "codex exec",
    },
)
if runner_payload_check.returncode != 0:
    raise SystemExit(runner_payload_check.stderr or runner_payload_check.stdout)
runner_payload = json.loads(runner_payload_check.stdout)
if runner_payload.get("messageText") != "Summarize today's progress":
    raise SystemExit("runner payload messageText mismatch")
if runner_payload.get("runnerCommand") != "codex exec":
    raise SystemExit("runner payload runnerCommand mismatch")
print("ok: feishu codex runner payload check passed")

cli_check = subprocess.run(
    ["node", "-c", str(repo_root / "scripts" / "feishu-codex.js")],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    check=False,
)
if cli_check.returncode != 0:
    raise SystemExit(cli_check.stderr or cli_check.stdout)
print("ok: feishu codex cli syntax check passed")

cli_help_check = subprocess.run(
    ["node", str(repo_root / "scripts" / "feishu-codex.js"), "help"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    check=False,
    cwd=str(repo_root),
)
if cli_help_check.returncode != 0 or "Commands:" not in cli_help_check.stdout:
    raise SystemExit(cli_help_check.stderr or cli_help_check.stdout or "cli help failed")
for required in ["auth", "start", "stop", "restart", "status"]:
    if required not in cli_help_check.stdout:
        raise SystemExit(f"cli help missing service command: {required}")
print("ok: feishu codex cli help check passed")

cli_runner_check = subprocess.run(
    ["node", str(repo_root / "scripts" / "feishu-codex.js"), "runner", "--print-payload"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    check=False,
    cwd=str(repo_root),
    env={
        **__import__("os").environ,
        "FEISHU_MESSAGE_TEXT": "CLI runner message",
        "FEISHU_SESSION_KEY": "chat:cli",
        "FEISHU_SESSION_WORKSPACE": str(repo_root),
        "FEISHU_RUNNER_COMMAND": "codex exec",
    },
)
if cli_runner_check.returncode != 0:
    raise SystemExit(cli_runner_check.stderr or cli_runner_check.stdout)
cli_runner_payload = json.loads(cli_runner_check.stdout)
if cli_runner_payload.get("messageText") != "CLI runner message":
    raise SystemExit("cli runner payload mismatch")
print("ok: feishu codex cli runner check passed")

cli_webhook_check = subprocess.run(
    ["node", str(repo_root / "scripts" / "feishu-codex.js"), "webhook", "--self-test"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    check=False,
    cwd=str(repo_root),
)
if cli_webhook_check.returncode != 0 or "ok: webhook self-test passed" not in cli_webhook_check.stdout:
    raise SystemExit(cli_webhook_check.stderr or cli_webhook_check.stdout or "cli webhook self-test failed")
print("ok: feishu codex cli webhook check passed")

service_check = subprocess.run(
    [
        "node",
        "-e",
        """
const fs = require('fs');
const os = require('os');
const path = require('path');
const service = require('./scripts/feishu-service.js');

process.env.FEISHU_BOT_STATE_DIR = fs.mkdtempSync(path.join(os.tmpdir(), 'feishu-service-'));
process.env.FEISHU_SERVICE_LABEL = 'com.hunkwu.feishu-codex.bot';

const config = service.getServiceConfig();
service.writeLaunchdConfig(config);

const plist = fs.readFileSync(config.plistPath, 'utf8');
if (!plist.includes('<string>com.hunkwu.feishu-codex.bot</string>')) {
  throw new Error('plist missing label');
}
if (!plist.includes(config.stdoutLog) || !plist.includes(config.stderrLog)) {
  throw new Error('plist missing log paths');
}
if (!plist.includes(config.botScriptPath)) {
  throw new Error('plist missing bot script path');
}

const metadata = service.readServiceMetadata(config);
if (!metadata || metadata.mode !== 'launchd' || metadata.stdout_log !== config.stdoutLog) {
  throw new Error(`unexpected service metadata: ${JSON.stringify(metadata)}`);
}

const status = service.formatServiceStatus({
  label: config.label,
  mode: 'launchd',
  platformSupported: true,
  launchctlAvailable: true,
  loaded: false,
  launchctlState: 'not_loaded',
  pid: '',
  stateDir: config.stateDir,
  stdoutLog: config.stdoutLog,
  stderrLog: config.stderrLog,
  plistPath: config.plistPath,
  lastStartedAt: '',
  lastStoppedAt: '',
});
if (!status.includes('Service label: com.hunkwu.feishu-codex.bot')) {
  throw new Error('service status formatting missing label');
}
if (!status.includes('Launchctl loaded: no')) {
  throw new Error('service status formatting missing launchctl loaded state');
}

console.log('ok: service config checks passed');
        """,
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    check=False,
    cwd=str(repo_root),
)
if service_check.returncode != 0:
    raise SystemExit(service_check.stderr or service_check.stdout)
print(service_check.stdout.strip())

access_control_check = subprocess.run(
    [
        "node",
        "-e",
        """
const bot = require('./plugins/feishu/scripts/feishu-long-connection-bot.js');

const event = {
  sender: {
    sender_id: { open_id: 'ou_blocked_user' },
    sender_type: 'user',
  },
  message: {
    message_id: 'om_acl_test',
    chat_id: 'oc_acl_test',
    chat_type: 'group',
    message_type: 'text',
    content: JSON.stringify({ text: 'run this task' }),
  },
};

const allowedByChat = bot.authorizeMessage(event, {
  ownerOpenId: '',
  admins: new Set(),
  allowedUsers: new Set(),
  allowedChats: new Set(['oc_acl_test']),
});
if (!allowedByChat.allowed || allowedByChat.reason !== 'allowed_chat') {
  throw new Error(`expected allowed_chat authorization, got ${JSON.stringify(allowedByChat)}`);
}

const unconfigured = bot.authorizeMessage(event, {
  ownerOpenId: '',
  admins: new Set(),
  allowedUsers: new Set(),
  allowedChats: new Set(),
});
if (unconfigured.allowed || unconfigured.reason !== 'access_not_configured') {
  throw new Error(`expected access_not_configured, got ${JSON.stringify(unconfigured)}`);
}
const unconfiguredMessage = bot.buildAccessDeniedMessage({
  ownerOpenId: '',
  admins: new Set(),
  allowedUsers: new Set(),
  allowedChats: new Set(),
});
if (!unconfiguredMessage.includes('local execution is disabled') || unconfiguredMessage.includes('App Secret')) {
  throw new Error(`unexpected unconfigured message: ${unconfiguredMessage}`);
}

const blocked = bot.authorizeMessage(event, {
  ownerOpenId: 'ou_owner',
  admins: new Set(['ou_admin']),
  allowedUsers: new Set(['ou_allowed']),
  allowedChats: new Set(),
});
if (blocked.allowed || blocked.reason !== 'not_allowed') {
  throw new Error(`expected blocked authorization, got ${JSON.stringify(blocked)}`);
}

const deniedMessage = bot.buildAccessDeniedMessage({
  ownerOpenId: 'ou_owner',
  admins: new Set(['ou_admin']),
  allowedUsers: new Set(['ou_allowed']),
  allowedChats: new Set(['oc_acl_test']),
}, {
  chatId: 'oc_acl_test',
  senderOpenId: 'ou_blocked_user',
});
if (!deniedMessage.includes('owner') || !deniedMessage.includes('allowed chats') || !deniedMessage.includes('Current chat_id: oc_acl_test')) {
  throw new Error(`unexpected denied message: ${deniedMessage}`);
}
if (!deniedMessage.includes('FEISHU_BOT_ALLOWED_USERS="ou_blocked_user"')) {
  throw new Error(`denied message should include allowlist hint: ${deniedMessage}`);
}

console.log('ok: access control checks passed');
        """,
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    check=False,
    cwd=str(repo_root),
)
if access_control_check.returncode != 0:
    raise SystemExit(access_control_check.stderr or access_control_check.stdout)
print(access_control_check.stdout.strip())

queue_check = subprocess.run(
    [
        "node",
        "-e",
        """
const fs = require('fs');
const os = require('os');
const path = require('path');
const bot = require('./plugins/feishu/scripts/feishu-long-connection-bot.js');

process.env.FEISHU_BOT_STATE_DIR = fs.mkdtempSync(path.join(os.tmpdir(), 'feishu-bot-queue-'));
process.env.FEISHU_DEFAULT_WORKSPACE = process.cwd();
process.env.FEISHU_BOT_ALLOWED_CHATS = 'oc_test_chat';

const sessionKey = 'chat:oc_test_chat';
const queued = bot.enqueueMessage(bot.createDefaultSession(sessionKey), 'second task', 'om_second');
if (!Array.isArray(queued.queuedMessages) || queued.queuedMessages.length !== 1) {
  throw new Error(`expected one queued message, got ${JSON.stringify(queued)}`);
}
if (queued.status !== 'queued') {
  throw new Error(`expected queued status, got ${queued.status}`);
}

const dequeued = bot.dequeueMessage(queued);
if (!dequeued.nextItem || dequeued.nextItem.text !== 'second task') {
  throw new Error(`unexpected dequeued item: ${JSON.stringify(dequeued)}`);
}
if (dequeued.session.queuedMessages.length !== 0) {
  throw new Error('expected empty queue after dequeue');
}
if (!bot.formatStatus(queued, true).includes('Queued: 1')) {
  throw new Error('status should show queued count');
}

console.log('ok: queue state checks passed');
        """,
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    check=False,
    cwd=str(repo_root),
)
if queue_check.returncode != 0:
    raise SystemExit(queue_check.stderr or queue_check.stdout)
print(queue_check.stdout.strip())

batch_queue_check = subprocess.run(
    [
        "node",
        "-e",
        """
const fs = require('fs');
const os = require('os');
const path = require('path');
const bot = require('./plugins/feishu/scripts/feishu-long-connection-bot.js');

const sessionKey = 'chat:batch';
process.env.FEISHU_BOT_STATE_DIR = fs.mkdtempSync(path.join(os.tmpdir(), 'feishu-bot-batch-'));
process.env.FEISHU_DEFAULT_WORKSPACE = process.cwd();
process.env.FEISHU_BOT_BATCH_WINDOW_MS = '500';

let session = bot.createDefaultSession(sessionKey);
session = bot.enqueueMessage(session, 'first queued', 'om_1');
session = bot.enqueueMessage(session, 'second queued', 'om_2');
session = bot.enqueueMessage(session, 'third queued', 'om_3');

const saved = bot.loadSession(sessionKey);
saved.queuedMessages[0].queuedAt = '2026-06-03T10:00:00.000Z';
saved.queuedMessages[1].queuedAt = '2026-06-03T10:00:00.200Z';
saved.queuedMessages[2].queuedAt = '2026-06-03T10:00:01.200Z';
bot.saveSession(saved);

const taken = bot.takeQueuedBatch(bot.loadSession(sessionKey), 500);
if (taken.batchItems.length !== 2) {
  throw new Error(`expected first batch size 2, got ${taken.batchItems.length}`);
}
if (!bot.buildQueuedPrompt(taken.batchItems).includes('Queued Message 2')) {
  throw new Error('expected combined queued prompt');
}
if (taken.session.queuedMessages.length !== 1) {
  throw new Error(`expected one message left after first batch, got ${taken.session.queuedMessages.length}`);
}

const takenSecond = bot.takeQueuedBatch(bot.loadSession(sessionKey), 500);
if (takenSecond.batchItems.length !== 1 || takenSecond.batchItems[0].text !== 'third queued') {
  throw new Error(`unexpected second batch: ${JSON.stringify(takenSecond)}`);
}

console.log('ok: queue batch checks passed');
        """,
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    check=False,
    cwd=str(repo_root),
)
if batch_queue_check.returncode != 0:
    raise SystemExit(batch_queue_check.stderr or batch_queue_check.stdout)
print(batch_queue_check.stdout.strip())

bot_bridge_check = subprocess.run(
    [
        "node",
        "-e",
        """
const fs = require('fs');
const os = require('os');
const path = require('path');
const bot = require('./plugins/feishu/scripts/feishu-long-connection-bot.js');

const fixture = JSON.parse(fs.readFileSync('./plugins/feishu/testdata/webhook/message_receive_v1.json', 'utf8'));
const event = fixture.event;
const queuedEvent = JSON.parse(JSON.stringify(fixture.event));
queuedEvent.message.message_id = 'om_test_message_2';
queuedEvent.message.content = JSON.stringify({ text: '第二条排队消息' });
const queuedEvent3 = JSON.parse(JSON.stringify(fixture.event));
queuedEvent3.message.message_id = 'om_test_message_3';
queuedEvent3.message.content = JSON.stringify({ text: '第三条排队消息' });
const replies = [];
const runtime = {
  children: new Map(),
  hasRunning(sessionKey) {
    return this.children.has(sessionKey);
  },
  setRunning(sessionKey, child) {
    this.children.set(sessionKey, child);
  },
  clearRunning(sessionKey) {
    this.children.delete(sessionKey);
  },
  stop(sessionKey) {
    const child = this.children.get(sessionKey);
    if (!child) return false;
    child.kill('SIGTERM');
    return true;
  },
};

process.env.FEISHU_BOT_STATE_DIR = fs.mkdtempSync(path.join(os.tmpdir(), 'feishu-bot-bridge-'));
process.env.FEISHU_DEFAULT_WORKSPACE = process.cwd();
process.env.FEISHU_CODEX_COMMAND = 'node plugins/feishu/scripts/feishu-codex-runner.js';
process.env.FEISHU_RUNNER_COMMAND = 'node plugins/feishu/scripts/feishu-codex-echo.js';
process.env.FEISHU_CODEX_COMMAND_MODE = 'env';
process.env.FEISHU_BOT_ALLOWED_CHATS = 'oc_test_chat';
process.env.FEISHU_BOT_BATCH_WINDOW_MS = '0';

const client = {
  im: {
    v1: {
      message: {
        create: async ({ data }) => {
          replies.push(JSON.parse(data.content).text);
          return { data: { message_id: 'om_reply_test' } };
        },
      },
    },
  },
};

(async () => {
  const firstRun = bot.handleTextMessage(client, event, runtime);
  await new Promise((resolve) => setTimeout(resolve, 50));
  const queuedResult = await bot.handleTextMessage(client, queuedEvent, runtime);
  const queuedResult2 = await bot.handleTextMessage(client, queuedEvent3, runtime);
  const result = await firstRun;
  if (!result || !['execution', 'execution_with_queue'].includes(result.mode)) {
    throw new Error(`unexpected bot result: ${JSON.stringify(result)}`);
  }
  if (!queuedResult || queuedResult.mode !== 'queued') {
    throw new Error(`unexpected queued result: ${JSON.stringify(queuedResult)}`);
  }
  if (!queuedResult2 || queuedResult2.mode !== 'queued') {
    throw new Error(`unexpected second queued result: ${JSON.stringify(queuedResult2)}`);
  }
  if (replies.length !== 5) {
    throw new Error(`expected five replies, got ${replies.length}`);
  }
  const firstReply = replies.find((item) => item.includes('Message: 请总结今天的项目进展'));
  const queueNotice = replies.find((item) => item.includes('Your message has been queued.'));
  const queueNotice2 = replies.filter((item) => item.includes('Your message has been queued.'));
  const queuedReply = replies.find((item) => item.includes('Queued task completed.'));
  const queuedReply2 = replies.filter((item) => item.includes('Queued task completed.'));
  if (!firstReply || !firstReply.includes('Feishu Codex Echo')) {
    throw new Error(`first reply missing echo marker: ${JSON.stringify(replies)}`);
  }
  if (!firstReply.includes('Session: chat:oc_test_chat')) {
    throw new Error(`first reply missing session key: ${firstReply}`);
  }
  if (!queueNotice || !queueNotice.includes('Queued: 1')) {
    throw new Error(`queue notice missing queued marker: ${JSON.stringify(replies)}`);
  }
  if (queueNotice2.length !== 2 || !queueNotice2.some((item) => item.includes('Queued: 2'))) {
    throw new Error(`expected two queue notices with growing count: ${JSON.stringify(replies)}`);
  }
  if (!queueNotice.includes('Runner command: node plugins/feishu/scripts/feishu-codex-echo.js')) {
    throw new Error(`queue notice missing runner command: ${JSON.stringify(replies)}`);
  }
  if (!queuedReply || !queuedReply.includes('Message: 第二条排队消息')) {
    throw new Error(`queued reply missing second message text: ${JSON.stringify(replies)}`);
  }
  if (queuedReply2.length !== 2 || !queuedReply2.some((item) => item.includes('Message: 第三条排队消息'))) {
    throw new Error(`expected second queued reply: ${JSON.stringify(replies)}`);
  }
  const idsReply = await bot.handleCommand({ name: 'ids', argText: '', raw: '/ids' }, bot.loadSession('chat:oc_test_chat'), runtime, {
    chatId: 'oc_test_chat',
    senderOpenId: 'ou_test_sender',
  });
  if (!idsReply.includes('Chat ID: oc_test_chat') || !idsReply.includes('Sender Open ID: ou_test_sender')) {
    throw new Error(`unexpected ids reply: ${idsReply}`);
  }
  console.log('ok: bot bridge end-to-end local check passed');
})().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
        """,
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    check=False,
    cwd=str(repo_root),
)
if bot_bridge_check.returncode != 0:
    raise SystemExit(bot_bridge_check.stderr or bot_bridge_check.stdout)
print(bot_bridge_check.stdout.strip())

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

digest_check = subprocess.run(
    ["node", "-c", str(plugin_dir / "scripts" / "feishu-daily-digest.js")],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    check=False,
)
if digest_check.returncode != 0:
    raise SystemExit(digest_check.stderr or digest_check.stdout)
print("ok: lightweight digest syntax check passed")
PY

if ! FEISHU_APP_ID=cli_xxx FEISHU_APP_SECRET=xxx FEISHU_DEFAULT_RECEIVE_ID=ou_xxxxx FEISHU_DEFAULT_RECEIVE_ID_TYPE=open_id \
  node "${PLUGIN_DIR}/scripts/feishu-project-update.js" --help >/tmp/feishu-project-update-help.txt; then
  fail "project update help command failed"
fi
ok "project update help path passed"

if ! FEISHU_APP_ID=cli_xxx FEISHU_APP_SECRET=xxx FEISHU_DEFAULT_RECEIVE_ID=ou_xxxxx FEISHU_DEFAULT_RECEIVE_ID_TYPE=open_id FEISHU_DEFAULT_UPDATE_MODE=weekly \
  node "${PLUGIN_DIR}/scripts/feishu-project-update.js" --preview --file "${PLUGIN_DIR}/skills/feishu/examples/project-update-template.md" >/tmp/feishu-project-update-preview.txt; then
  fail "project update preview command failed"
fi
ok "project update preview path passed"

if ! FEISHU_APP_ID=cli_xxx FEISHU_APP_SECRET=xxx FEISHU_DEFAULT_RECEIVE_ID=ou_xxxxx FEISHU_DEFAULT_RECEIVE_ID_TYPE=open_id FEISHU_DEFAULT_UPDATE_MODE=daily \
  node "${PLUGIN_DIR}/scripts/feishu-project-update.js" --dry-run-json --message "Completed: shipped docs." >/tmp/feishu-project-update-json.txt; then
  fail "project update dry-run-json command failed"
fi
ok "project update dry-run-json path passed"

if FEISHU_APP_ID=cli_xxx FEISHU_APP_SECRET=xxx FEISHU_DEFAULT_RECEIVE_ID=ou_xxxxx FEISHU_DEFAULT_RECEIVE_ID_TYPE=bad \
  node "${PLUGIN_DIR}/scripts/feishu-project-update.js" --preview --message "test" >/tmp/feishu-project-update-invalid.txt 2>&1; then
  fail "project update invalid receive_id_type should fail"
fi
if ! rg -q "Invalid receive_id_type" /tmp/feishu-project-update-invalid.txt; then
  fail "project update invalid receive_id_type message missing"
fi
ok "project update invalid receive_id_type path passed"

if FEISHU_APP_ID=cli_xxx FEISHU_APP_SECRET=xxx \
  "${PLUGIN_DIR}/scripts/doctor-feishu-auth.sh" >/tmp/feishu-doctor-no-access.txt 2>&1; then
  fail "doctor should block missing bot access control"
else
  doctor_status=$?
  if [[ "${doctor_status}" -ne 2 ]]; then
    fail "doctor missing access control should exit 2, got ${doctor_status}"
  fi
fi
if ! rg -q "explicit bot allowlist" /tmp/feishu-doctor-no-access.txt; then
  fail "doctor missing access control hint missing"
fi
ok "doctor fail-closed access control path passed"

python3 - <<'PY' "${REPO_ROOT}"
import importlib.util
import contextlib
import io
import json
import pathlib
import subprocess
import sys
import tempfile

repo_root = pathlib.Path(sys.argv[1])
script_dir = repo_root / "plugins" / "feishu" / "scripts"
sys.path.insert(0, str(script_dir))
spec = importlib.util.spec_from_file_location("feishu_project_report", script_dir / "feishu-project-report.py")
report_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report_module)

parser = report_module.build_parser()
options = parser.parse_args(["--mode", "custom", "--workspace", str(repo_root)])
problems = report_module.validate_options(options)
if not any("--since is required" in item for item in problems):
    raise SystemExit(f"custom mode validation missing: {problems}")

options = parser.parse_args(["--max-sources", "6", "--workspace", str(repo_root)])
problems = report_module.validate_options(options)
if not any("--max-sources" in item for item in problems):
    raise SystemExit(f"max sources validation missing: {problems}")

git_options = parser.parse_args(["--mode", "weekly", "--workspace", str(repo_root)])
git_context = report_module.collect_git_context(repo_root, git_options)
if not git_context["project"] or not git_context["branch"]:
    raise SystemExit(f"invalid Git context: {git_context}")

with tempfile.TemporaryDirectory(prefix="feishu-empty-git-") as temp_dir:
    subprocess.run(["git", "init", "-q"], cwd=temp_dir, check=True)
    empty_options = parser.parse_args(["--mode", "daily", "--workspace", temp_dir])
    empty_context = report_module.collect_git_context(pathlib.Path(temp_dir), empty_options)
    if empty_context["head"] != "unborn" or empty_context["commits"]:
        raise SystemExit(f"unborn Git repository was not handled: {empty_context}")

valid_report = {
    "title": "Test",
    "summary": "Summary",
    "status": "In Progress",
    "completed": ["One"],
    "in_progress": ["Two"],
    "risks": [],
    "next_steps": ["Three"],
    "sources": [],
}
report_module.validate_report(valid_report)
try:
    report_module.validate_report({**valid_report, "status": "Unknown"})
except RuntimeError:
    pass
else:
    raise SystemExit("invalid report status should fail")

blocks = report_module.report_to_blocks(valid_report, [])
if not any(item.get("heading2") for item in blocks) or not any(item.get("bullet") for item in blocks):
    raise SystemExit(f"report blocks are incomplete: {blocks}")

class FakeClient:
    def request(self, method, path, **kwargs):
        if path.endswith("/search/object"):
            return {"data": {"docs_entities": [{"docs_token": "dox_test_1", "title": "Doc One"}]}}
        if path.endswith("/raw_content"):
            return {"data": {"content": "x" * 40000}}
        raise AssertionError((method, path, kwargs))

original_client = report_module.client
report_module.client = FakeClient()
sources = report_module.collect_feishu_sources(["project"], 3)
report_module.client = original_client
if len(sources) != 1 or len(sources[0]["content"]) != report_module.MAX_CONTEXT_CHARS or not sources[0]["truncated"]:
    raise SystemExit(f"source truncation failed: {sources}")

class FakeWikiClient:
    def request(self, method, path, **kwargs):
        if path.endswith("/search/object"):
            return {"data": {"docs_entities": []}}
        if path.endswith("/nodes/search"):
            return {"data": {"items": [{"node_token": "wik_test", "title": "Wiki One"}]}}
        if path.endswith("/spaces/get_node"):
            return {"data": {"node": {"obj_type": "docx", "obj_token": "dox_wiki", "title": "Wiki One"}}}
        if path.endswith("/raw_content"):
            return {"data": {"content": "wiki content"}}
        raise AssertionError((method, path, kwargs))

report_module.client = FakeWikiClient()
wiki_sources = report_module.collect_feishu_sources(["project"], 3)
report_module.client = original_client
if len(wiki_sources) != 1 or wiki_sources[0]["kind"] != "wiki" or wiki_sources[0]["token"] != "dox_wiki":
    raise SystemExit(f"Wiki fallback failed: {wiki_sources}")

original_run_command = report_module.run_command
def timeout_command(*args, **kwargs):
    raise subprocess.TimeoutExpired(cmd="codex", timeout=1)
report_module.run_command = timeout_command
try:
    report_module.generate_report(git_context, [], git_options)
except subprocess.TimeoutExpired:
    pass
else:
    raise SystemExit("Codex timeout should propagate")
finally:
    report_module.run_command = original_run_command

calls = []
original_create_document = report_module.create_document
original_create_bitable = report_module.create_bitable_record
original_send = report_module.send_message
report_module.create_document = lambda report, sources: calls.append("doc") or {"document_id": "doc", "url": "url"}
def fail_bitable(report, git_context):
    calls.append("bitable")
    raise RuntimeError("bitable failed")
report_module.create_bitable_record = fail_bitable
report_module.send_message = lambda report, document: calls.append("send") or {"message_id": "message"}
write_options = parser.parse_args(["--write-doc", "--bitable", "--send", "--confirm"])
try:
    with contextlib.redirect_stderr(io.StringIO()):
        report_module.execute_writes(write_options, valid_report, [], git_context)
except RuntimeError:
    pass
else:
    raise SystemExit("expected Bitable failure")
finally:
    report_module.create_document = original_create_document
    report_module.create_bitable_record = original_create_bitable
    report_module.send_message = original_send
if calls != ["doc", "bitable"]:
    raise SystemExit(f"message should not send after Bitable failure: {calls}")

print("ok: project report workflow checks passed")
PY

python3 - <<'PY' "${REPO_ROOT}"
import importlib.util
import pathlib
import sys

repo_root = pathlib.Path(sys.argv[1])
mcp_path = repo_root / "plugins" / "feishu" / "scripts" / "feishu_http_mcp.py"
spec = importlib.util.spec_from_file_location("feishu_http_mcp_test", mcp_path)
mcp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mcp)

calls = []
class FakeClient:
    def request(self, method, path, **kwargs):
        calls.append((method, path, kwargs))
        return {"code": 0, "data": {}}

mcp.client = FakeClient()
mcp.handle_tool_call("docx_v1_document_create", {"data": {"title": "Report"}, "useUAT": True})
mcp.handle_tool_call("docx_v1_documentBlockChildren_create", {
    "path": {"document_id": "doc", "block_id": "doc"},
    "data": {"children": []},
    "useUAT": True,
})
mcp.handle_tool_call("drive_v1_meta_batchQuery", {"data": {"request_docs": []}, "useUAT": True})
mcp.handle_tool_call("bitable_v1_appTableRecord_create", {
    "path": {"app_token": "base", "table_id": "table"},
    "data": {"fields": {}},
    "useUAT": True,
})

expected_paths = [
    "/open-apis/docx/v1/documents",
    "/open-apis/docx/v1/documents/doc/blocks/doc/children",
    "/open-apis/drive/v1/metas/batch_query",
    "/open-apis/bitable/v1/apps/base/tables/table/records",
]
if [item[1] for item in calls] != expected_paths:
    raise SystemExit(f"unexpected MCP routes: {calls}")
if any(item[2].get("token_mode") != "user" for item in calls):
    raise SystemExit(f"new MCP write tools must default to user token mode: {calls}")
print("ok: MCP write tool routes and token modes passed")
PY

python3 - <<'PY' "${REPO_ROOT}"
import importlib.util
import os
import pathlib
import tempfile
import sys

repo_root = pathlib.Path(sys.argv[1])
mcp_path = repo_root / "plugins" / "feishu" / "scripts" / "feishu_http_mcp.py"
spec = importlib.util.spec_from_file_location("feishu_http_mcp_refresh_test", mcp_path)
mcp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mcp)

with tempfile.TemporaryDirectory() as temp_dir:
    env_path = pathlib.Path(temp_dir) / ".env"
    env_path.write_text(
        "\n".join([
            "FEISHU_APP_ID=cli_xxx",
            "FEISHU_APP_SECRET=secret",
            "FEISHU_USER_ACCESS_TOKEN=old-token",
            "FEISHU_USER_REFRESH_TOKEN=refresh-token",
        ]) + "\n",
        encoding="utf-8",
    )
    os.environ["FEISHU_APP_ID"] = "cli_xxx"
    os.environ["FEISHU_APP_SECRET"] = "secret"
    os.environ["FEISHU_USER_ACCESS_TOKEN"] = "old-token"
    os.environ["FEISHU_USER_REFRESH_TOKEN"] = "refresh-token"
    os.environ["FEISHU_ENV_FILE"] = str(env_path)

    client = mcp.FeishuClient()
    calls = []

    def fake_raw(method, path, *, query=None, body=None, auth_token=None):
        calls.append((method, path, auth_token, body))
        if len(calls) == 1:
            raise mcp.FeishuError("Authentication token expired. Please request a new one.", payload={
                "code": 99991663,
                "msg": "Authentication token expired. Please request a new one.",
            })
        if path == "/open-apis/authen/v2/oauth/token":
            return {
                "code": 0,
                "access_token": "new-token",
                "refresh_token": "new-refresh-token",
            }
        return {"code": 0, "data": {"ok": True}}

    client._raw_request = fake_raw
    payload = client.request("GET", "/open-apis/authen/v1/user_info", token_mode="user")
    if payload.get("data", {}).get("ok") is not True:
        raise SystemExit("refresh retry did not return final payload")
    if [item[1] for item in calls] != [
        "/open-apis/authen/v1/user_info",
        "/open-apis/authen/v2/oauth/token",
        "/open-apis/authen/v1/user_info",
    ]:
        raise SystemExit(f"unexpected refresh call order: {calls}")
    text = env_path.read_text(encoding="utf-8")
    if "FEISHU_USER_ACCESS_TOKEN=new-token" not in text or "FEISHU_USER_REFRESH_TOKEN=new-refresh-token" not in text:
        raise SystemExit("refreshed tokens were not persisted")

print("ok: user token auto-refresh path passed")
PY

if ! python3 "${PLUGIN_DIR}/scripts/feishu-project-report.py" --help >/tmp/feishu-report-help.txt; then
  fail "project report help failed"
fi
if ! rg -q -- "--write-doc" /tmp/feishu-report-help.txt; then
  fail "project report help missing --write-doc"
fi
ok "project report help path passed"

if ! FEISHU_APP_ID=cli_xxx FEISHU_APP_SECRET=xxx FEISHU_DEFAULT_RECEIVE_ID=ou_xxxxx FEISHU_DEFAULT_RECEIVE_ID_TYPE=open_id \
  node "${PLUGIN_DIR}/scripts/feishu-daily-digest.js" --preview >/tmp/feishu-daily-digest-preview.txt 2>&1; then
  fail "lightweight digest preview command failed"
fi
if ! rg -q "Digest template:" /tmp/feishu-daily-digest-preview.txt; then
  fail "lightweight digest preview missing template header"
fi
if ! rg -q "Codex 日报" /tmp/feishu-daily-digest-preview.txt; then
  fail "lightweight digest preview missing Chinese title"
fi
if ! rg -q "已完成:" /tmp/feishu-daily-digest-preview.txt; then
  fail "lightweight digest preview missing completed section"
fi
ok "lightweight digest preview path passed"

if ! node "${REPO_ROOT}/scripts/feishu-codex.js" help >/tmp/feishu-codex-help.txt; then
  fail "feishu CLI help command failed"
fi
if ! rg -q "digest" /tmp/feishu-codex-help.txt; then
  fail "feishu CLI help missing digest command"
fi
if ! rg -q "auth" /tmp/feishu-codex-help.txt; then
  fail "feishu CLI help missing auth command"
fi
ok "feishu CLI digest help path passed"

"${REPO_ROOT}/scripts/check-sensitive-values.sh"

echo "Smoke test passed."
