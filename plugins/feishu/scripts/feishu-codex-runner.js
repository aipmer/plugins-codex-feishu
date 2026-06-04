#!/usr/bin/env node
require('dotenv').config({ quiet: true });

const { spawn } = require('child_process');

const DEFAULT_COMMAND = 'codex exec';
const HELP_TEXT = `Usage:
  node plugins/feishu/scripts/feishu-codex-runner.js
  FEISHU_RUNNER_COMMAND="codex exec" node plugins/feishu/scripts/feishu-codex-runner.js
  FEISHU_MESSAGE_TEXT="Summarize today's progress" node plugins/feishu/scripts/feishu-codex-runner.js --print-payload

Options:
  --help            Show this help text.
  --print-payload   Print the normalized payload as JSON and exit.

Environment:
  FEISHU_RUNNER_COMMAND     Downstream local command. Defaults to "codex exec".
  FEISHU_MESSAGE_TEXT       Raw text from Feishu.
  FEISHU_MESSAGE_PAYLOAD    JSON payload from the bot bridge when FEISHU_CODEX_COMMAND_MODE=env.
  FEISHU_SESSION_KEY        Session identifier.
  FEISHU_SESSION_WORKSPACE  Workspace bound to the current session.
  FEISHU_RUN_ID             Current run identifier.
`;

function parseArgs(argv) {
  const options = {
    help: false,
    printPayload: false,
  };

  for (const arg of argv) {
    if (arg === '--help' || arg === '-h') {
      options.help = true;
    } else if (arg === '--print-payload') {
      options.printPayload = true;
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  return options;
}

function readStdin() {
  return new Promise((resolve, reject) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => {
      data += chunk;
    });
    process.stdin.on('end', () => resolve(data));
    process.stdin.on('error', reject);
  });
}

function parsePayloadEnv() {
  const raw = (process.env.FEISHU_MESSAGE_PAYLOAD || '').trim();
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw);
  } catch (error) {
    throw new Error(`Invalid FEISHU_MESSAGE_PAYLOAD JSON: ${error.message}`);
  }
}

function normalizePromptPayload(stdinText, payloadFromEnv) {
  const sessionKey = (process.env.FEISHU_SESSION_KEY || payloadFromEnv?.sessionKey || '').trim();
  const workspace = (process.env.FEISHU_SESSION_WORKSPACE || payloadFromEnv?.workspace || process.cwd()).trim();
  const rawMessage = (process.env.FEISHU_MESSAGE_TEXT || payloadFromEnv?.text || '').trim();
  const prompt = stdinText.trim() || [
    `Session: ${sessionKey || 'unknown'}`,
    `Workspace: ${workspace}`,
    '',
    rawMessage,
  ].join('\n').trim();

  return {
    sessionKey,
    workspace,
    messageText: rawMessage,
    prompt,
    runId: (process.env.FEISHU_RUN_ID || '').trim(),
  };
}

function getRunnerCommand() {
  return (process.env.FEISHU_RUNNER_COMMAND || DEFAULT_COMMAND).trim() || DEFAULT_COMMAND;
}

async function runCommand(command, payload) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, {
      cwd: payload.workspace || process.cwd(),
      env: {
        ...process.env,
        FEISHU_SESSION_KEY: payload.sessionKey,
        FEISHU_SESSION_WORKSPACE: payload.workspace,
        FEISHU_MESSAGE_TEXT: payload.messageText,
        FEISHU_RUN_ID: payload.runId,
      },
      shell: true,
      stdio: ['pipe', 'pipe', 'pipe'],
    });

    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (chunk) => {
      stdout += chunk.toString();
    });
    child.stderr.on('data', (chunk) => {
      stderr += chunk.toString();
    });
    child.on('error', (error) => {
      reject(new Error(`Failed to start downstream command "${command}": ${error.message}`));
    });
    child.on('close', (code, signal) => {
      if (signal) {
        reject(new Error(`Downstream command stopped with signal ${signal}`));
        return;
      }
      if (code !== 0) {
        reject(new Error(stderr.trim() || stdout.trim() || `Downstream command exited with code ${code}`));
        return;
      }
      resolve(stdout.trim() || 'Downstream command completed with no output.');
    });

    child.stdin.write(payload.prompt);
    child.stdin.end();
  });
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    console.log(HELP_TEXT);
    return;
  }

  const stdinText = await readStdin();
  const payloadFromEnv = parsePayloadEnv();
  const payload = normalizePromptPayload(stdinText, payloadFromEnv);

  if (!payload.prompt.trim()) {
    throw new Error('No Feishu message payload found. Provide stdin content or FEISHU_MESSAGE_TEXT / FEISHU_MESSAGE_PAYLOAD.');
  }

  if (options.printPayload) {
    console.log(JSON.stringify({
      ...payload,
      runnerCommand: getRunnerCommand(),
    }, null, 2));
    return;
  }

  const output = await runCommand(getRunnerCommand(), payload);
  console.log(output);
}

if (require.main === module) {
  main().catch((error) => {
    console.error(error.message);
    process.exit(1);
  });
}

module.exports = {
  normalizePromptPayload,
  parseArgs,
  parsePayloadEnv,
  readStdin,
  runCommand,
};
