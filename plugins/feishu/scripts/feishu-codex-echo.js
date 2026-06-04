#!/usr/bin/env node

async function readStdin() {
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

async function main() {
  const stdin = (await readStdin()).trim();
  const payload = (process.env.FEISHU_MESSAGE_PAYLOAD || '').trim();
  const messageText = (process.env.FEISHU_MESSAGE_TEXT || '').trim();
  const sessionKey = (process.env.FEISHU_SESSION_KEY || '').trim();
  const workspace = (process.env.FEISHU_SESSION_WORKSPACE || '').trim();
  const runId = (process.env.FEISHU_RUN_ID || '').trim();

  const lines = [
    'Feishu Codex Echo',
    `Session: ${sessionKey || 'unknown'}`,
    `Workspace: ${workspace || process.cwd()}`,
    `Run: ${runId || 'none'}`,
  ];

  if (messageText) {
    lines.push(`Message: ${messageText}`);
  }
  if (payload) {
    lines.push(`Payload: ${payload}`);
  }
  if (stdin) {
    lines.push('Stdin:');
    lines.push(stdin);
  }

  process.stdout.write(`${lines.join('\n')}\n`);
}

if (require.main === module) {
  main().catch((error) => {
    console.error(error.message);
    process.exit(1);
  });
}
