#!/usr/bin/env node
require('dotenv').config({ quiet: true });

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const DEFAULT_TEMPLATE_FILE = path.join(
  __dirname,
  '..',
  'skills',
  'feishu',
  'examples',
  'project-update-template.md',
);

function parseArgs(argv) {
  const options = {
    confirm: false,
    file: (process.env.FEISHU_DIGEST_TEMPLATE_FILE || '').trim(),
    help: false,
    preview: false,
    receiveId: '',
    receiveIdType: '',
    send: false,
    title: '',
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === '--confirm') {
      options.confirm = true;
    } else if (arg === '--file') {
      options.file = argv[++index] || '';
    } else if (arg === '--help' || arg === '-h') {
      options.help = true;
    } else if (arg === '--preview') {
      options.preview = true;
    } else if (arg === '--receive-id') {
      options.receiveId = argv[++index] || '';
    } else if (arg === '--receive-id-type') {
      options.receiveIdType = argv[++index] || '';
    } else if (arg === '--send') {
      options.send = true;
    } else if (arg === '--title') {
      options.title = argv[++index] || '';
    } else {
      throw new Error(`Unknown argument: ${arg}`);
    }
  }

  if (!options.preview && !options.send) {
    options.preview = true;
  }

  return options;
}

function usage() {
  return `Usage:
  npm run feishu -- digest --preview
  npm run feishu -- digest --send --confirm
  npm run feishu -- digest --preview --file ./plugins/feishu/skills/feishu/examples/project-update-template.md
  npm run feishu -- digest --send --confirm --title "Codex 日报"

Options:
  --preview                 Render a local digest preview. Default mode.
  --send                    Send the digest through the existing push flow.
  --confirm                 Required for real sends.
  --file <path>             Override the default digest template file.
  --title <text>            Override the default title.
  --receive-id <id>         Override FEISHU_DEFAULT_RECEIVE_ID.
  --receive-id-type <type>  Override FEISHU_DEFAULT_RECEIVE_ID_TYPE.
`;
}

function formatDate(date = new Date()) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function defaultTitle() {
  return `Codex 日报 ${formatDate()}`;
}

function resolveTemplateFile(optionValue) {
  const filePath = optionValue.trim() || DEFAULT_TEMPLATE_FILE;
  return path.resolve(process.cwd(), filePath);
}

function renderTemplate(raw, title) {
  return raw
    .replaceAll('{{DATE}}', formatDate())
    .replaceAll('{{TITLE}}', title);
}

function invokeProjectUpdate(options, renderedBody, title) {
  const scriptPath = path.join(__dirname, 'feishu-project-update.js');
  const args = [scriptPath];

  if (options.send) {
    args.push('--send');
  }
  if (options.confirm) {
    args.push('--confirm');
  }
  if (!options.send || options.preview) {
    args.push('--preview');
  }

  args.push('--mode', 'daily');
  args.push('--title', title);
  args.push('--message', renderedBody);

  if (options.receiveId.trim()) {
    args.push('--receive-id', options.receiveId.trim());
  }
  if (options.receiveIdType.trim()) {
    args.push('--receive-id-type', options.receiveIdType.trim());
  }

  return spawnSync(process.execPath, args, {
    stdio: 'inherit',
    env: process.env,
    cwd: process.cwd(),
    shell: false,
  });
}

function main() {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    console.log(usage());
    return;
  }

  const title = (options.title || defaultTitle()).trim();
  const templateFile = resolveTemplateFile(options.file);
  const rawTemplate = fs.readFileSync(templateFile, 'utf8').trim();
  const renderedBody = renderTemplate(rawTemplate, title);

  if (!renderedBody) {
    throw new Error(`Digest template is empty: ${templateFile}`);
  }

  if (!options.send) {
    console.error(`Digest template: ${templateFile}`);
    console.error(`Digest title: ${title}`);
  }

  const result = invokeProjectUpdate(options, renderedBody, title);
  if (result.error) {
    throw result.error;
  }
  process.exit(result.status === null ? 1 : result.status);
}

if (require.main === module) {
  try {
    main();
  } catch (error) {
    console.error(error.message);
    process.exit(1);
  }
}

module.exports = {
  DEFAULT_TEMPLATE_FILE,
  defaultTitle,
  formatDate,
  parseArgs,
  renderTemplate,
  resolveTemplateFile,
  usage,
};
