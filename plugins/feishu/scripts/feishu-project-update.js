#!/usr/bin/env node
require('dotenv').config({ quiet: true });

const fs = require('fs');
const path = require('path');
const Lark = require('@larksuiteoapi/node-sdk');

const DEFAULT_TEST_TEXT = 'Codex 飞书私人助理测试消息。';
const VALID_MODES = new Set(['daily', 'weekly', 'custom']);
const VALID_RECEIVE_ID_TYPES = new Set(['open_id', 'chat_id']);
const SECTION_ALIASES = new Map([
  ['Completed', '已完成'],
  ['In Progress', '进行中'],
  ['Risks', '风险阻塞'],
  ['Next Steps', '下一步'],
  ['已完成', '已完成'],
  ['进行中', '进行中'],
  ['风险阻塞', '风险阻塞'],
  ['下一步', '下一步'],
]);
const SECTION_ORDER = ['已完成', '进行中', '风险阻塞', '下一步'];

function parseArgs(argv) {
  const options = {
    confirm: false,
    dryRunJson: false,
    file: '',
    help: false,
    message: '',
    mode: (process.env.FEISHU_DEFAULT_UPDATE_MODE || 'custom').trim() || 'custom',
    receiveId: process.env.FEISHU_DEFAULT_RECEIVE_ID || '',
    receiveIdType: process.env.FEISHU_DEFAULT_RECEIVE_ID_TYPE || 'open_id',
    send: false,
    test: false,
    title: '',
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--confirm') {
      options.confirm = true;
    } else if (arg === '--dry-run-json') {
      options.dryRunJson = true;
    } else if (arg === '--file') {
      options.file = argv[++index] || '';
    } else if (arg === '--help' || arg === '-h') {
      options.help = true;
    } else if (arg === '--message') {
      options.message = argv[++index] || '';
    } else if (arg === '--mode') {
      options.mode = argv[++index] || '';
    } else if (arg === '--preview') {
      options.send = false;
    } else if (arg === '--receive-id') {
      options.receiveId = argv[++index] || '';
    } else if (arg === '--receive-id-type') {
      options.receiveIdType = argv[++index] || '';
    } else if (arg === '--send') {
      options.send = true;
    } else if (arg === '--test') {
      options.test = true;
    } else if (arg === '--title') {
      options.title = argv[++index] || '';
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  return options;
}

function usage() {
  return `Usage:
  npm run feishu:project-update -- --preview --mode daily --file ./plugins/feishu/skills/feishu/examples/project-update-template.md
  npm run feishu:project-update -- --dry-run-json --mode weekly --message "已完成: 发布文档"
  npm run feishu:project-update -- --test --send --confirm
  npm run feishu:project-update -- --send --confirm --title "Codex 周报" --file ./digest.md

Options:
  --preview                 Render a local preview. Default when --confirm is absent.
  --dry-run-json            Print the outgoing Feishu payload as JSON.
  --send                    Prepare to send the message. Requires --confirm.
  --confirm                 Required for real sends.
  --test                    Send a short connectivity test message.
  --message <text>          Message body.
  --file <path>             Read message body from a UTF-8 text file.
  --mode <mode>             daily, weekly, or custom.
  --title <text>            Override the generated title line.
  --receive-id <id>         Recipient open_id or chat_id. Defaults to FEISHU_DEFAULT_RECEIVE_ID.
  --receive-id-type <type>  open_id or chat_id. Defaults to FEISHU_DEFAULT_RECEIVE_ID_TYPE.
`;
}

function envValue(name) {
  return (process.env[name] || '').trim();
}

function readBody(options) {
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

function defaultTitleForMode(mode) {
  if (mode === 'daily') return 'Codex 日报';
  if (mode === 'weekly') return 'Codex 周报';
  return 'Codex 项目更新';
}

function normalizeSections(body) {
  const sections = new Map(SECTION_ORDER.map((label) => [label, []]));
  let current = '已完成';

  for (const rawLine of body.split('\n')) {
    const line = rawLine.trim();
    if (!line) {
      continue;
    }

    const normalizedHeader = line.endsWith(':') || line.endsWith('：')
      ? line.slice(0, -1).trim()
      : '';
    const matchedLabel = normalizedHeader ? SECTION_ALIASES.get(normalizedHeader) : '';
    if (matchedLabel) {
      current = matchedLabel;
      continue;
    }

    if (line.startsWith('- ') || line.startsWith('* ')) {
      sections.get(current).push(line.slice(2).trim());
      continue;
    }

    sections.get(current).push(line);
  }

  return sections;
}

function renderSection(label, items) {
  const lines = items.length ? items.map((item) => `- ${item}`) : ['- 无'];
  return `${label}:\n${lines.join('\n')}`;
}

function buildRenderedMessage(options, body) {
  if (options.test) {
    return DEFAULT_TEST_TEXT;
  }

  const title = (options.title || defaultTitleForMode(options.mode)).trim();
  const sections = normalizeSections(body);
  return [
    title,
    '',
    renderSection('已完成', sections.get('已完成')),
    '',
    renderSection('进行中', sections.get('进行中')),
    '',
    renderSection('风险阻塞', sections.get('风险阻塞')),
    '',
    renderSection('下一步', sections.get('下一步')),
  ].join('\n');
}

function buildPayload(options, renderedMessage) {
  return {
    receive_id_type: options.receiveIdType,
    receive_id: options.receiveId.trim(),
    msg_type: 'text',
    content: {
      text: renderedMessage,
    },
  };
}

function validate(options, body) {
  const problems = [];

  if (!envValue('FEISHU_APP_ID')) {
    problems.push('Missing FEISHU_APP_ID.');
  }
  if (!envValue('FEISHU_APP_SECRET')) {
    problems.push('Missing FEISHU_APP_SECRET.');
  }
  if (!options.receiveId.trim()) {
    problems.push('Missing FEISHU_DEFAULT_RECEIVE_ID or --receive-id.');
  }
  if (!body) {
    problems.push('Missing update content. Use --message, --file, or --test.');
  }
  if (!VALID_RECEIVE_ID_TYPES.has(options.receiveIdType)) {
    problems.push('Invalid receive_id_type. Use open_id or chat_id.');
  }
  if (!VALID_MODES.has(options.mode)) {
    problems.push('Invalid mode. Use daily, weekly, or custom.');
  }
  if (options.send && !options.confirm) {
    problems.push('Real sends require --confirm. Without it, the command stays in preview mode.');
  }

  return problems;
}

function printConfigGuide(problems) {
  console.error('Feishu private assistant push is not ready yet.');
  console.error('');
  console.error('Problems:');
  for (const problem of problems) {
    console.error(`- ${problem}`);
  }
  console.error('');
  console.error('Fix:');
  console.error('1. Copy .env.example to .env and set FEISHU_APP_ID / FEISHU_APP_SECRET.');
  console.error('2. Set FEISHU_DEFAULT_RECEIVE_ID and FEISHU_DEFAULT_RECEIVE_ID_TYPE.');
  console.error('3. Use open_id for private assistant push, or chat_id for chat delivery.');
  console.error('4. Run npm run feishu:doctor.');
  console.error('5. Run npm run feishu:project-update -- --test --send --confirm before sending a full update.');
  console.error('');
  console.error('Troubleshooting hints:');
  console.error('- Permission errors usually mean the app lacks Feishu IM scopes or tenant approval.');
  console.error('- "No permission" after send often means the bot is not published or the recipient is outside app visibility.');
  console.error('- FEISHU_APP_ID identifies the sending app. open_id identifies the recipient user.');
}

function printPreview(payload, options, renderedMessage) {
  if (options.dryRunJson) {
    console.log(JSON.stringify(payload, null, 2));
    return;
  }

  console.log('Preview only. Add --send --confirm to send.');
  console.log('');
  console.log(`Receive ID type: ${payload.receive_id_type}`);
  console.log(`Receive ID: ${payload.receive_id}`);
  console.log('');
  console.log(renderedMessage);
}

function mapApiError(error) {
  const statusCode = error && error.response ? error.response.status : null;
  const data = error && error.response ? error.response.data : null;
  const code = data && Object.prototype.hasOwnProperty.call(data, 'code') ? data.code : null;
  const message = data && data.msg ? data.msg : error.message;

  if (statusCode === 403 || code === 99991663) {
    return 'Feishu rejected the request due to missing permissions. Check IM scopes and tenant approval.';
  }
  if (code === 230001 || code === 230006) {
    return 'The bot may not be published, or the recipient is outside app visibility.';
  }
  if (code === 10020 || code === 11020) {
    return 'The target receive_id is invalid for the selected receive_id_type.';
  }

  return `Feishu API error: ${message}`;
}

async function sendMessage(options, payload) {
  const client = new Lark.Client({
    appId: envValue('FEISHU_APP_ID'),
    appSecret: envValue('FEISHU_APP_SECRET'),
    appType: Lark.AppType.SelfBuild,
    domain: Lark.Domain.Feishu,
  });

  try {
    const response = await client.im.v1.message.create({
      params: {
        receive_id_type: payload.receive_id_type,
      },
      data: {
        receive_id: payload.receive_id,
        msg_type: payload.msg_type,
        content: JSON.stringify(payload.content),
      },
    });

    console.log(JSON.stringify({
      ok: true,
      receive_id_type: payload.receive_id_type,
      message_id: response && response.data ? response.data.message_id : null,
    }));
  } catch (error) {
    console.error(mapApiError(error));
    process.exit(1);
  }
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    console.log(usage());
    return;
  }

  const body = readBody(options);
  const problems = validate(options, body);
  if (problems.length) {
    printConfigGuide(problems);
    process.exit(2);
  }

  const renderedMessage = buildRenderedMessage(options, body);
  const payload = buildPayload(options, renderedMessage);

  if (!options.send || !options.confirm) {
    printPreview(payload, options, renderedMessage);
    return;
  }

  await sendMessage(options, payload);
}

if (require.main === module) {
  main().catch((error) => {
    console.error(error.message);
    process.exit(1);
  });
}

module.exports = {
  buildPayload,
  buildRenderedMessage,
  normalizeSections,
  parseArgs,
  validate,
};
