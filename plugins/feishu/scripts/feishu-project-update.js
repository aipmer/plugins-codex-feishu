#!/usr/bin/env node
require('dotenv').config({ quiet: true });

const fs = require('fs');
const path = require('path');
const Lark = require('@larksuiteoapi/node-sdk');

const DEFAULT_TEST_TEXT = 'Codex Feishu private assistant test message.';

function parseArgs(argv) {
  const options = {
    send: false,
    test: false,
    message: '',
    file: '',
    receiveId: process.env.FEISHU_DEFAULT_RECEIVE_ID || '',
    receiveIdType: process.env.FEISHU_DEFAULT_RECEIVE_ID_TYPE || 'open_id',
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--send') {
      options.send = true;
    } else if (arg === '--preview') {
      options.send = false;
    } else if (arg === '--test') {
      options.test = true;
    } else if (arg === '--message') {
      options.message = argv[++index] || '';
    } else if (arg === '--file') {
      options.file = argv[++index] || '';
    } else if (arg === '--receive-id') {
      options.receiveId = argv[++index] || '';
    } else if (arg === '--receive-id-type') {
      options.receiveIdType = argv[++index] || '';
    } else if (arg === '--help' || arg === '-h') {
      options.help = true;
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  return options;
}

function usage() {
  return `Usage:
  npm run feishu:project-update -- --preview --message "Project update"
  npm run feishu:project-update -- --preview --file ./digest.md
  npm run feishu:project-update -- --test --send
  npm run feishu:project-update -- --send --file ./digest.md

Options:
  --preview                 Print the outgoing message without sending. Default.
  --send                    Send the message to Feishu.
  --test                    Send a short test message.
  --message <text>          Message body.
  --file <path>             Read message body from a UTF-8 text file.
  --receive-id <id>         Recipient open_id or chat_id. Defaults to FEISHU_DEFAULT_RECEIVE_ID.
  --receive-id-type <type>  open_id or chat_id. Defaults to FEISHU_DEFAULT_RECEIVE_ID_TYPE.
`;
}

function envValue(name) {
  return (process.env[name] || '').trim();
}

function buildMessage(options) {
  if (options.test) {
    return DEFAULT_TEST_TEXT;
  }
  if (options.message.trim()) {
    return options.message.trim();
  }
  if (options.file.trim()) {
    const filePath = path.resolve(process.cwd(), options.file.trim());
    return fs.readFileSync(filePath, 'utf8').trim();
  }
  return '';
}

function validate(options, message) {
  const missing = [];
  if (!envValue('FEISHU_APP_ID')) missing.push('FEISHU_APP_ID');
  if (!envValue('FEISHU_APP_SECRET')) missing.push('FEISHU_APP_SECRET');
  if (!options.receiveId.trim()) missing.push('FEISHU_DEFAULT_RECEIVE_ID or --receive-id');
  if (!message) missing.push('--message, --file, or --test');

  if (!['open_id', 'chat_id'].includes(options.receiveIdType)) {
    missing.push('valid --receive-id-type open_id|chat_id');
  }

  return missing;
}

function printConfigGuide(missing) {
  console.error('Feishu private assistant push is not configured yet.');
  console.error('');
  console.error('Missing or invalid:');
  for (const item of missing) {
    console.error(`- ${item}`);
  }
  console.error('');
  console.error('Fix:');
  console.error('1. Copy .env.example to .env and set FEISHU_APP_ID / FEISHU_APP_SECRET.');
  console.error('2. Get the recipient user open_id from Feishu event logs or email lookup.');
  console.error('3. Set FEISHU_DEFAULT_RECEIVE_ID=ou_xxxxx and FEISHU_DEFAULT_RECEIVE_ID_TYPE=open_id.');
  console.error('4. Run npm run feishu:doctor.');
  console.error('5. Run npm run feishu:project-update -- --test --send before sending a full update.');
  console.error('');
  console.error('Reminder: FEISHU_APP_ID identifies the sending app. open_id identifies the recipient user.');
}

async function sendMessage(options, message) {
  const client = new Lark.Client({
    appId: envValue('FEISHU_APP_ID'),
    appSecret: envValue('FEISHU_APP_SECRET'),
    appType: Lark.AppType.SelfBuild,
    domain: Lark.Domain.Feishu,
  });

  const response = await client.im.v1.message.create({
    params: {
      receive_id_type: options.receiveIdType,
    },
    data: {
      receive_id: options.receiveId.trim(),
      msg_type: 'text',
      content: JSON.stringify({ text: message }),
    },
  });

  console.log(JSON.stringify({
    ok: true,
    receive_id_type: options.receiveIdType,
    message_id: response && response.data ? response.data.message_id : null,
  }));
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    console.log(usage());
    return;
  }

  const message = buildMessage(options);
  const missing = validate(options, message);
  if (missing.length) {
    printConfigGuide(missing);
    process.exit(2);
  }

  if (!options.send) {
    console.log(JSON.stringify({
      mode: 'preview',
      receive_id_type: options.receiveIdType,
      receive_id: options.receiveId.trim(),
      msg_type: 'text',
      content: { text: message },
    }, null, 2));
    return;
  }

  await sendMessage(options, message);
}

if (require.main === module) {
  main().catch((error) => {
    console.error(error.message);
    process.exit(1);
  });
}

module.exports = {
  buildMessage,
  parseArgs,
  validate,
};
