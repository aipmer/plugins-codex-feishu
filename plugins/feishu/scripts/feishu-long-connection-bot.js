#!/usr/bin/env node
require('dotenv').config({ quiet: true });

const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawn } = require('child_process');
const Lark = require('@larksuiteoapi/node-sdk');

const DEFAULT_REPLY_TEXT = '收到，我已接入 Codex Feishu 插件。';
const DEFAULT_TIMEOUT_MS = 10 * 60 * 1000;
const DEFAULT_MAX_OUTPUT_CHARS = 4000;
const DEFAULT_STATE_DIR = path.join(os.homedir(), '.codex-feishu', 'state');
const DEFAULT_COMMAND_MODE = 'stdin';
const DEFAULT_BATCH_WINDOW_MS = 0;
const MAX_RECENT_MESSAGE_IDS = 50;
const HELP_TEXT = [
  'Feishu for Codex commands:',
  '/help - show available commands',
  '/new - reset current session state',
  '/status - show workspace and run status',
  '/ids - show current chat and sender identifiers',
  '/stop - stop the current local task',
  '/cd <path> - change workspace for this session',
].join('\n');

function requiredEnv(name) {
  const value = (process.env[name] || '').trim();
  if (!value) {
    throw new Error(`${name} is required`);
  }
  return value;
}

function parseTextContent(content) {
  if (!content || typeof content !== 'string') {
    return '';
  }
  try {
    const parsed = JSON.parse(content);
    return parsed && typeof parsed.text === 'string' ? parsed.text.trim() : '';
  } catch (error) {
    return '';
  }
}

function getSenderType(data) {
  return data && data.sender ? data.sender.sender_type || '' : '';
}

function getMessage(data) {
  return data && data.message ? data.message : {};
}

function getSenderOpenId(data) {
  const sender = data && data.sender ? data.sender : {};
  const senderId = sender.sender_id || {};
  return (senderId.open_id || '').trim();
}

function extractSessionKey(data) {
  const message = getMessage(data);
  const senderOpenId = getSenderOpenId(data);

  if (message.chat_id) {
    return `chat:${message.chat_id}`;
  }
  if (senderOpenId) {
    return `user:${senderOpenId}`;
  }
  return '';
}

function parseIdList(value) {
  return new Set(
    (value || '')
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean)
  );
}

function getAccessControlConfig() {
  return {
    ownerOpenId: (process.env.FEISHU_BOT_OWNER_OPEN_ID || '').trim(),
    allowedChats: parseIdList(process.env.FEISHU_BOT_ALLOWED_CHATS || ''),
    allowedUsers: parseIdList(process.env.FEISHU_BOT_ALLOWED_USERS || ''),
    admins: parseIdList(process.env.FEISHU_BOT_ADMINS || ''),
  };
}

function isAccessControlled(config) {
  return Boolean(
    config.ownerOpenId ||
    config.allowedChats.size ||
    config.allowedUsers.size ||
    config.admins.size
  );
}

function authorizeMessage(data, config = getAccessControlConfig()) {
  const message = getMessage(data);
  const chatId = (message.chat_id || '').trim();
  const senderOpenId = getSenderOpenId(data);

  if (!isAccessControlled(config)) {
    return { allowed: true, reason: 'open' };
  }

  if (config.allowedChats.has(chatId)) {
    return { allowed: true, reason: 'allowed_chat' };
  }

  if (!senderOpenId) {
    return { allowed: false, reason: 'missing_sender_open_id' };
  }

  if (senderOpenId === config.ownerOpenId) {
    return { allowed: true, reason: 'owner' };
  }

  if (config.admins.has(senderOpenId)) {
    return { allowed: true, reason: 'admin' };
  }

  if (config.allowedUsers.has(senderOpenId)) {
    return { allowed: true, reason: 'allowed_user' };
  }

  return { allowed: false, reason: 'not_allowed' };
}

function buildAccessDeniedMessage(config = getAccessControlConfig(), context = {}) {
  if (!isAccessControlled(config)) {
    return 'Access control is not configured.';
  }

  const enabled = [];
  if (config.ownerOpenId) enabled.push('owner');
  if (config.admins.size) enabled.push('admins');
  if (config.allowedUsers.size) enabled.push('allowed users');
  if (config.allowedChats.size) enabled.push('allowed chats');

  const lines = [
    `Access denied for this message. Active policy: ${enabled.join(', ')}.`,
  ];
  if (context.chatId) {
    lines.push(`Current chat_id: ${context.chatId}`);
  }
  if (context.senderOpenId) {
    lines.push(`Current sender open_id: ${context.senderOpenId}`);
  }
  if (context.chatId) {
    lines.push(`Allow this chat: FEISHU_BOT_ALLOWED_CHATS="${context.chatId}"`);
  }
  if (context.senderOpenId) {
    lines.push(`Allow this user: FEISHU_BOT_ALLOWED_USERS="${context.senderOpenId}"`);
  }
  return lines.join('\n');
}

function shouldHandleMessage(data) {
  const message = getMessage(data);
  if (getSenderType(data) && getSenderType(data) !== 'user') {
    return false;
  }
  if (!['group', 'p2p'].includes(message.chat_type)) {
    return false;
  }
  if (message.message_type !== 'text') {
    return false;
  }
  return Boolean(extractSessionKey(data));
}

function parseCommand(text) {
  const trimmed = (text || '').trim();
  if (!trimmed.startsWith('/')) {
    return null;
  }

  const firstSpace = trimmed.indexOf(' ');
  const name = (firstSpace === -1 ? trimmed.slice(1) : trimmed.slice(1, firstSpace)).trim().toLowerCase();
  const argText = firstSpace === -1 ? '' : trimmed.slice(firstSpace + 1).trim();

  if (!['help', 'new', 'status', 'ids', 'stop', 'cd'].includes(name)) {
    return { name: 'unknown', argText, raw: trimmed };
  }

  return { name, argText, raw: trimmed };
}

function sanitizeSessionKey(sessionKey) {
  return sessionKey.replace(/[^a-zA-Z0-9._-]/g, '_');
}

function getStateDir() {
  return path.resolve((process.env.FEISHU_BOT_STATE_DIR || DEFAULT_STATE_DIR).trim() || DEFAULT_STATE_DIR);
}

function ensureStateDir(stateDir) {
  fs.mkdirSync(stateDir, { recursive: true });
}

function getSessionFilePath(sessionKey, stateDir = getStateDir()) {
  ensureStateDir(stateDir);
  return path.join(stateDir, `${sanitizeSessionKey(sessionKey)}.json`);
}

function getDefaultWorkspace() {
  const configured = (process.env.FEISHU_DEFAULT_WORKSPACE || '').trim();
  return path.resolve(configured || process.cwd());
}

function createDefaultSession(sessionKey) {
  return {
    sessionKey,
    workspace: getDefaultWorkspace(),
    running: false,
    status: 'idle',
    queuedMessages: [],
    recentMessageIds: [],
    currentRunId: '',
    currentPid: null,
    currentStartedAt: '',
    stopRequested: false,
    lastCommand: '',
    lastMessage: '',
    lastResult: '',
    lastError: '',
    updatedAt: new Date().toISOString(),
  };
}

function loadSession(sessionKey, stateDir = getStateDir()) {
  const filePath = getSessionFilePath(sessionKey, stateDir);
  if (!fs.existsSync(filePath)) {
    return createDefaultSession(sessionKey);
  }
  const parsed = JSON.parse(fs.readFileSync(filePath, 'utf8'));
  return { ...createDefaultSession(sessionKey), ...parsed, sessionKey };
}

function saveSession(session, stateDir = getStateDir()) {
  const filePath = getSessionFilePath(session.sessionKey, stateDir);
  const nextSession = {
    ...session,
    recentMessageIds: normalizeRecentMessageIds(session.recentMessageIds),
    updatedAt: new Date().toISOString(),
  };
  fs.writeFileSync(filePath, `${JSON.stringify(nextSession, null, 2)}\n`, 'utf8');
  return nextSession;
}

function resetSession(sessionKey, stateDir = getStateDir()) {
  const nextSession = createDefaultSession(sessionKey);
  return saveSession(nextSession, stateDir);
}

function getServiceStatusSummary() {
  try {
    const service = require(path.join(__dirname, '..', '..', '..', 'scripts', 'feishu-service.js'));
    return service.getServiceStatus();
  } catch (error) {
    return null;
  }
}

function buildIdsReply(context = {}) {
  return [
    `Session: ${context.sessionKey || 'unknown'}`,
    `Chat ID: ${context.chatId || 'unknown'}`,
    `Sender Open ID: ${context.senderOpenId || 'unknown'}`,
    '',
    'Whitelist examples:',
    `FEISHU_BOT_ALLOWED_CHATS="${context.chatId || 'oc_xxxxx'}"`,
    `FEISHU_BOT_ALLOWED_USERS="${context.senderOpenId || 'ou_xxxxx'}"`,
  ].join('\n');
}

function formatStatus(session, hasRunningProcess, context = {}) {
  const running = session.running && hasRunningProcess;
  const serviceStatus = context.serviceStatus || null;
  const runnerCommand = context.runnerCommand || process.env.FEISHU_RUNNER_COMMAND || '';
  const lines = [
    `Session: ${session.sessionKey}`,
    `Workspace: ${session.workspace}`,
    `Running: ${running ? 'yes' : 'no'}`,
    `Status: ${session.status || (running ? 'running' : 'idle')}`,
    `Queued: ${Array.isArray(session.queuedMessages) ? session.queuedMessages.length : 0}`,
    `Current PID: ${session.currentPid || 'none'}`,
    `Last command: ${session.lastCommand || 'none'}`,
  ];
  if (context.chatId) {
    lines.push(`Chat ID: ${context.chatId}`);
  }
  if (context.senderOpenId) {
    lines.push(`Sender Open ID: ${context.senderOpenId}`);
  }
  lines.push(`Command mode: ${getExecutionMode()}`);
  lines.push(`Bridge command: ${getExecutionCommand() || 'unconfigured'}`);
  lines.push(`Runner command: ${runnerCommand || 'default codex exec'}`);
  if (serviceStatus) {
    lines.push(`Service loaded: ${serviceStatus.loaded ? 'yes' : 'no'}`);
    lines.push(`Service state: ${serviceStatus.launchctlState || 'unknown'}`);
    lines.push(`Service PID: ${serviceStatus.pid || 'none'}`);
  }
  lines.push(`Last updated: ${session.updatedAt || 'unknown'}`);
  return lines.join('\n');
}

function normalizeRecentMessageIds(value) {
  if (!Array.isArray(value)) {
    return [];
  }

  const seen = new Set();
  const normalized = [];
  for (const item of value) {
    if (typeof item !== 'string') {
      continue;
    }
    const trimmed = item.trim();
    if (!trimmed || seen.has(trimmed)) {
      continue;
    }
    seen.add(trimmed);
    normalized.push(trimmed);
    if (normalized.length >= MAX_RECENT_MESSAGE_IDS) {
      break;
    }
  }

  return normalized;
}

function hasProcessedMessage(session, messageId) {
  const current = (messageId || '').trim();
  if (!current) {
    return false;
  }
  return normalizeRecentMessageIds(session.recentMessageIds).includes(current);
}

function markMessageProcessed(session, messageId) {
  const current = (messageId || '').trim();
  if (!current) {
    return session;
  }

  const nextIds = [
    current,
    ...normalizeRecentMessageIds(session.recentMessageIds).filter((item) => item !== current),
  ].slice(0, MAX_RECENT_MESSAGE_IDS);

  return saveSession({
    ...session,
    recentMessageIds: nextIds,
  });
}

function resolveWorkspace(inputPath, currentWorkspace) {
  const raw = (inputPath || '').trim();
  if (!raw) {
    throw new Error('Usage: /cd <path>');
  }
  const resolved = path.resolve(currentWorkspace || getDefaultWorkspace(), raw);
  const stat = fs.statSync(resolved, { throwIfNoEntry: false });
  if (!stat || !stat.isDirectory()) {
    throw new Error(`Workspace not found: ${resolved}`);
  }
  return resolved;
}

function truncateOutput(text, maxLength = DEFAULT_MAX_OUTPUT_CHARS) {
  const normalized = (text || '').trim();
  if (!normalized) {
    return '';
  }
  if (normalized.length <= maxLength) {
    return normalized;
  }
  return `${normalized.slice(0, maxLength)}\n...[truncated]`;
}

function getExecutionCommand() {
  return (process.env.FEISHU_CODEX_COMMAND || '').trim();
}

function getExecutionMode() {
  const mode = (process.env.FEISHU_CODEX_COMMAND_MODE || DEFAULT_COMMAND_MODE).trim().toLowerCase();
  return ['stdin', 'env'].includes(mode) ? mode : DEFAULT_COMMAND_MODE;
}

function getTimeoutMs() {
  const raw = Number.parseInt(process.env.FEISHU_CODEX_TIMEOUT_MS || '', 10);
  return Number.isFinite(raw) && raw > 0 ? raw : DEFAULT_TIMEOUT_MS;
}

function getBatchWindowMs() {
  const raw = Number.parseInt(process.env.FEISHU_BOT_BATCH_WINDOW_MS || '', 10);
  return Number.isFinite(raw) && raw >= 0 ? raw : DEFAULT_BATCH_WINDOW_MS;
}

function buildExecutionPrompt(text, session) {
  return [
    `Session: ${session.sessionKey}`,
    `Workspace: ${session.workspace}`,
    '',
    text.trim(),
  ].join('\n');
}

function buildExecutionArgs(text, session) {
  return JSON.stringify({
    sessionKey: session.sessionKey,
    workspace: session.workspace,
    text: text.trim(),
  });
}

function createRunId() {
  return `run_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

function normalizeQueuedMessages(value) {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .filter((item) => item && typeof item.text === 'string')
    .map((item) => ({
      text: item.text.trim(),
      sourceMessageId: item.sourceMessageId || null,
      queuedAt: item.queuedAt || new Date().toISOString(),
    }))
    .filter((item) => item.text);
}

function enqueueMessage(session, text, sourceMessageId) {
  const queuedMessages = normalizeQueuedMessages(session.queuedMessages);
  queuedMessages.push({
    text: text.trim(),
    sourceMessageId: sourceMessageId || null,
    queuedAt: new Date().toISOString(),
  });
  return saveSession({
    ...session,
    status: 'queued',
    queuedMessages,
  });
}

function buildQueuedPrompt(items) {
  return items
    .map((item, index) => `Queued Message ${index + 1}:\n${item.text}`)
    .join('\n\n');
}

function dequeueMessage(session) {
  const queuedMessages = normalizeQueuedMessages(session.queuedMessages);
  if (!queuedMessages.length) {
    return {
      nextItem: null,
      session: saveSession({
        ...session,
        queuedMessages: [],
      }),
    };
  }

  const [nextItem, ...rest] = queuedMessages;
  return {
    nextItem,
    session: saveSession({
      ...session,
      queuedMessages: rest,
    }),
  };
}

function takeQueuedBatch(session, batchWindowMs = getBatchWindowMs()) {
  const queuedMessages = normalizeQueuedMessages(session.queuedMessages);
  if (!queuedMessages.length) {
    return {
      batchItems: [],
      session: saveSession({
        ...session,
        queuedMessages: [],
      }),
    };
  }

  const first = queuedMessages[0];
  const firstTs = Date.parse(first.queuedAt || '') || 0;
  const batchItems = [first];
  let consumed = 1;

  if (batchWindowMs > 0 && firstTs > 0) {
    for (let index = 1; index < queuedMessages.length; index += 1) {
      const item = queuedMessages[index];
      const itemTs = Date.parse(item.queuedAt || '') || 0;
      if (!itemTs || itemTs - firstTs > batchWindowMs) {
        break;
      }
      batchItems.push(item);
      consumed += 1;
    }
  }

  const rest = queuedMessages.slice(consumed);
  return {
    batchItems,
    session: saveSession({
      ...session,
      queuedMessages: rest,
    }),
  };
}

function reconcileSession(session, runtime) {
  const runningInMemory = runtime.hasRunning(session.sessionKey);
  if (!session.running) {
    if (session.status === 'running') {
      return {
        ...session,
        status: 'idle',
        currentPid: null,
        currentRunId: '',
        currentStartedAt: '',
        stopRequested: false,
      };
    }
    return session;
  }

  if (runningInMemory) {
    return session;
  }

  return {
    ...session,
    running: false,
    status: session.stopRequested ? 'cancelled' : 'failed',
    currentPid: null,
    currentRunId: '',
    currentStartedAt: '',
    stopRequested: false,
    lastError: session.stopRequested
      ? (session.lastError || 'Previous local task was stopped.')
      : (session.lastError || 'Previous local task is no longer attached to the current bot process.'),
  };
}

function loadActiveSession(sessionKey, runtime, stateDir = getStateDir()) {
  const session = loadSession(sessionKey, stateDir);
  const reconciled = reconcileSession(session, runtime);
  if (JSON.stringify(reconciled) !== JSON.stringify(session)) {
    return saveSession(reconciled, stateDir);
  }
  return reconciled;
}

async function runLocalCommand(command, session, promptText, onSpawn) {
  if (!command) {
    return {
      ok: false,
      output: 'FEISHU_CODEX_COMMAND is not configured. Set a local command to turn Feishu messages into Codex runs.',
    };
  }

  return new Promise((resolve) => {
    const commandMode = getExecutionMode();
    const child = spawn(command, {
      cwd: session.workspace,
      env: {
        ...process.env,
        FEISHU_CODEX_COMMAND_MODE: commandMode,
        FEISHU_RUN_ID: session.currentRunId,
        FEISHU_SESSION_KEY: session.sessionKey,
        FEISHU_SESSION_WORKSPACE: session.workspace,
        FEISHU_MESSAGE_TEXT: promptText,
        FEISHU_MESSAGE_PAYLOAD: buildExecutionArgs(promptText, session),
      },
      shell: true,
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    if (typeof onSpawn === 'function') {
      onSpawn(child);
    }

    let stdout = '';
    let stderr = '';
    let finished = false;
    const timeout = setTimeout(() => {
      if (!finished) {
        child.kill('SIGTERM');
      }
    }, getTimeoutMs());

    child.stdout.on('data', (chunk) => {
      stdout += chunk.toString();
    });
    child.stderr.on('data', (chunk) => {
      stderr += chunk.toString();
    });
    child.on('error', (error) => {
      if (finished) {
        return;
      }
      finished = true;
      clearTimeout(timeout);
      resolve({
        ok: false,
        output: `Failed to start local command: ${error.message}`,
      });
    });

    child.on('close', (code, signal) => {
      if (finished) {
        return;
      }
      finished = true;
      clearTimeout(timeout);
      if (signal) {
        resolve({
          ok: false,
          output: `Local Codex task stopped with signal ${signal}.`,
        });
        return;
      }
      if (code !== 0) {
        resolve({
          ok: false,
          output: truncateOutput(stderr || stdout || `Local Codex task failed with exit code ${code}.`),
        });
        return;
      }
      resolve({
        ok: true,
        output: truncateOutput(stdout || 'Local Codex task completed with no output.'),
      });
    });

    if (commandMode === 'stdin') {
      child.stdin.write(buildExecutionPrompt(promptText, session));
    }
    child.stdin.end();
  });
}

async function executeSessionTask(sessionKey, text, sourceMessageId, runtime) {
  let session = loadActiveSession(sessionKey, runtime);
  session = saveSession({
    ...session,
    running: true,
    status: 'running',
    currentRunId: createRunId(),
    currentPid: null,
    currentStartedAt: new Date().toISOString(),
    stopRequested: false,
    lastMessage: text,
    lastError: '',
  });

  const commandText = getExecutionCommand();
  const result = await runLocalCommand(commandText, session, text, (child) => {
    runtime.setRunning(sessionKey, child);
    saveSession({
      ...loadSession(sessionKey),
      currentPid: child.pid || null,
    });
  });

  runtime.clearRunning(sessionKey);
  const latestSession = loadSession(sessionKey);
  const stopped = latestSession.stopRequested || /stopped with signal/i.test(result.output);
  session = saveSession({
    ...latestSession,
    running: false,
    status: result.ok ? 'completed' : (stopped ? 'cancelled' : 'failed'),
    currentPid: null,
    currentRunId: '',
    currentStartedAt: '',
    stopRequested: false,
    lastCommand: commandText || 'unconfigured',
    lastResult: result.ok ? result.output : '',
    lastError: result.ok ? '' : result.output,
  });

  const replyText = result.ok
    ? result.output
    : `${stopped ? 'Local task cancelled.' : 'Local task failed.'}\n${result.output}`;

  return {
    ok: result.ok,
    replyText,
    sourceMessageId: sourceMessageId || null,
    session,
    stopped,
  };
}

async function drainQueuedTasks(client, chatId, sessionKey, runtime) {
  const replies = [];
  let session = loadSession(sessionKey);

  while (normalizeQueuedMessages(session.queuedMessages).length) {
    const drained = takeQueuedBatch(session);
    session = drained.session;
    if (!drained.batchItems.length) {
      break;
    }

    const combinedText = drained.batchItems.length === 1
      ? drained.batchItems[0].text
      : buildQueuedPrompt(drained.batchItems);
    const sourceMessageId = drained.batchItems[drained.batchItems.length - 1].sourceMessageId || null;
    const execution = await executeSessionTask(sessionKey, combinedText, sourceMessageId, runtime);
    const prefix = drained.batchItems.length === 1
      ? 'Queued task completed.'
      : `Queued batch completed (${drained.batchItems.length} messages).`;
    const replyText = `${prefix}\n${execution.replyText}`;
    const replyMessageId = await sendTextReply(client, chatId, replyText);
    replies.push({
      replyMessageId,
      replyText,
      batchSize: drained.batchItems.length,
    });
    session = loadSession(sessionKey);
  }

  return replies;
}

async function sendTextReply(client, receiveId, text) {
  const content = JSON.stringify({ text: (text || DEFAULT_REPLY_TEXT).trim() || DEFAULT_REPLY_TEXT });
  const response = await client.im.v1.message.create({
    params: {
      receive_id_type: 'chat_id',
    },
    data: {
      receive_id: receiveId,
      msg_type: 'text',
      content,
    },
  });

  return response && response.data ? response.data.message_id : null;
}

class SessionRuntime {
  constructor() {
    this.children = new Map();
  }

  hasRunning(sessionKey) {
    return this.children.has(sessionKey);
  }

  setRunning(sessionKey, childRef) {
    this.children.set(sessionKey, childRef);
  }

  clearRunning(sessionKey) {
    this.children.delete(sessionKey);
  }

  stop(sessionKey) {
    const child = this.children.get(sessionKey);
    if (!child) {
      return false;
    }
    child.kill('SIGTERM');
    return true;
  }
}

async function handleCommand(command, session, runtime, context = {}) {
  if (command.name === 'help' || command.name === 'unknown') {
    if (command.name === 'unknown') {
      return `${HELP_TEXT}\n\nUnknown command: ${command.raw}`;
    }
    return HELP_TEXT;
  }

  if (command.name === 'new') {
    if (runtime.hasRunning(session.sessionKey)) {
      return 'A local task is still running. Use /stop first, then retry /new.';
    }
    resetSession(session.sessionKey);
    return 'Current session has been reset.';
  }

  if (command.name === 'status') {
    const latest = loadActiveSession(session.sessionKey, runtime);
    return formatStatus(latest, runtime.hasRunning(session.sessionKey), {
      ...context,
      serviceStatus: getServiceStatusSummary(),
      runnerCommand: process.env.FEISHU_RUNNER_COMMAND || '',
    });
  }

  if (command.name === 'ids') {
    return buildIdsReply({
      ...context,
      sessionKey: session.sessionKey,
    });
  }

  if (command.name === 'stop') {
    const stopped = runtime.stop(session.sessionKey);
    if (!stopped) {
      return 'No running task for this session.';
    }
    saveSession({
      ...loadSession(session.sessionKey),
      stopRequested: true,
      status: 'cancelling',
      lastCommand: command.raw,
    });
    return 'Stop signal sent to the current local task.';
  }

  if (command.name === 'cd') {
    if (runtime.hasRunning(session.sessionKey)) {
      return 'A local task is still running. Wait for it to finish or use /stop before changing workspace.';
    }
    const latest = loadActiveSession(session.sessionKey, runtime);
    const workspace = resolveWorkspace(command.argText, latest.workspace);
    const nextSession = saveSession({
      ...latest,
      workspace,
      lastCommand: command.raw,
      lastError: '',
    });
    return `Workspace updated.\n${formatStatus(nextSession, runtime.hasRunning(session.sessionKey), {
      ...context,
      serviceStatus: getServiceStatusSummary(),
      runnerCommand: process.env.FEISHU_RUNNER_COMMAND || '',
    })}`;
  }

  return HELP_TEXT;
}

async function handleTextMessage(client, data, runtime) {
  if (!shouldHandleMessage(data)) {
    return null;
  }

  const message = getMessage(data);
  const senderOpenId = getSenderOpenId(data);
  const accessConfig = getAccessControlConfig();
  const authorization = authorizeMessage(data, accessConfig);
  if (!authorization.allowed) {
    const replyMessageId = await sendTextReply(client, message.chat_id, buildAccessDeniedMessage(accessConfig, {
      chatId: message.chat_id || '',
      senderOpenId,
    }));
    return {
      event_type: 'im.message.receive_v1',
      chat_id: message.chat_id,
      source_message_id: message.message_id || null,
      reply_message_id: replyMessageId,
      session_key: extractSessionKey(data),
      mode: 'access_denied',
      reason: authorization.reason,
    };
  }

  const text = parseTextContent(message.content);
  const sessionKey = extractSessionKey(data);
  let session = loadActiveSession(sessionKey, runtime);
  if (hasProcessedMessage(session, message.message_id || '')) {
    return {
      event_type: 'im.message.receive_v1',
      chat_id: message.chat_id,
      source_message_id: message.message_id || null,
      reply_message_id: null,
      session_key: sessionKey,
      mode: 'duplicate_ignored',
    };
  }

  session = markMessageProcessed(session, message.message_id || '');
  const command = parseCommand(text);

  if (command) {
    const reply = await handleCommand(command, session, runtime, {
      chatId: message.chat_id || '',
      senderOpenId,
    });
    const replyMessageId = await sendTextReply(client, message.chat_id, reply);
    return {
      event_type: 'im.message.receive_v1',
      chat_id: message.chat_id,
      source_message_id: message.message_id || null,
      reply_message_id: replyMessageId,
      session_key: sessionKey,
      mode: 'command',
    };
  }

  if (runtime.hasRunning(sessionKey)) {
    const queuedSession = enqueueMessage(session, text, message.message_id || null);
    const replyMessageId = await sendTextReply(
      client,
      message.chat_id,
      `A local task is already running for this session. Your message has been queued.\n${formatStatus(queuedSession, true, {
        chatId: message.chat_id || '',
        senderOpenId,
        serviceStatus: getServiceStatusSummary(),
        runnerCommand: process.env.FEISHU_RUNNER_COMMAND || '',
      })}`
    );
    return {
      event_type: 'im.message.receive_v1',
      chat_id: message.chat_id,
      source_message_id: message.message_id || null,
      reply_message_id: replyMessageId,
      session_key: sessionKey,
      mode: 'queued',
    };
  }

  const execution = await executeSessionTask(sessionKey, text, message.message_id || null, runtime);
  const replyMessageId = await sendTextReply(client, message.chat_id, execution.replyText);
  const drainedReplies = await drainQueuedTasks(client, message.chat_id, sessionKey, runtime);
  const mode = drainedReplies.length ? 'execution_with_queue' : 'execution';

  return {
    event_type: 'im.message.receive_v1',
    chat_id: message.chat_id,
    source_message_id: message.message_id || null,
    reply_message_id: replyMessageId,
    session_key: sessionKey,
    mode,
    workspace: execution.session.workspace,
  };
}

async function start() {
  const baseConfig = {
    appId: requiredEnv('FEISHU_APP_ID'),
    appSecret: requiredEnv('FEISHU_APP_SECRET'),
    appType: Lark.AppType.SelfBuild,
    domain: Lark.Domain.Feishu,
  };

  ensureStateDir(getStateDir());

  const client = new Lark.Client(baseConfig);
  const wsClient = new Lark.WSClient({
    ...baseConfig,
    loggerLevel: Lark.LoggerLevel.info,
  });
  const runtime = new SessionRuntime();

  const eventDispatcher = new Lark.EventDispatcher({}).register({
    'im.message.receive_v1': async (data) => {
      const event = await handleTextMessage(client, data, runtime);
      if (event) {
        console.log(JSON.stringify(event));
      }
    },
  });

  console.log('Feishu long-connection bot starting...');
  console.log('Listening for im.message.receive_v1 text messages.');
  console.log(`State dir: ${getStateDir()}`);
  if (!getExecutionCommand()) {
    console.log('FEISHU_CODEX_COMMAND is not configured yet. Non-command messages will return a setup hint.');
  }
  console.log(`Command mode: ${getExecutionMode()}`);

  wsClient.start({ eventDispatcher });
}

if (require.main === module) {
  start().catch((error) => {
    console.error('Feishu long-connection bot failed:', error.message);
    process.exit(1);
  });
}

module.exports = {
  authorizeMessage,
  buildQueuedPrompt,
  buildAccessDeniedMessage,
  createDefaultSession,
  dequeueMessage,
  enqueueMessage,
  extractSessionKey,
  formatStatus,
  getSessionFilePath,
  hasProcessedMessage,
  handleCommand,
  handleTextMessage,
  loadActiveSession,
  loadSession,
  markMessageProcessed,
  normalizeRecentMessageIds,
  parseCommand,
  parseTextContent,
  resetSession,
  resolveWorkspace,
  saveSession,
  shouldHandleMessage,
  start,
  takeQueuedBatch,
  truncateOutput,
};
