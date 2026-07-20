#!/usr/bin/env node
require('dotenv').config({ quiet: true });

const path = require('path');
const { spawnSync } = require('child_process');

const HELP_TEXT = `Usage:
  node scripts/feishu-codex.js <command> [args...]
  npm run feishu -- <command> [args...]

Commands:
  bot       Run the Feishu long-connection bot
  digest    Render or send the lightweight daily digest
  doctor    Run auth and environment checks
  auth      Run localhost OAuth callback and write FEISHU_USER_ACCESS_TOKEN
  start     Start the Feishu bot via launchd
  stop      Stop the Feishu bot service
  restart   Restart the Feishu bot service
  status    Show the Feishu bot service status
  push      Run the project update push command
  report    Generate and optionally publish a Git-aware Feishu project report
  runner    Run the Feishu Codex runner
  webhook   Run the webhook receiver
  help      Show this help text

Examples:
  npm run feishu -- doctor
  npm run feishu -- auth
  npm run feishu -- digest --preview
  npm run feishu -- bot
  npm run feishu -- start
  npm run feishu -- status
  npm run feishu -- runner --print-payload
  npm run feishu -- report --preview --mode weekly --query "project name"
  npm run feishu -- push --preview --message "Completed: shipped docs."
  npm run feishu -- webhook --self-test
`;

const COMMANDS = {
  bot: {
    command: 'node',
    args: [path.join('plugins', 'feishu', 'scripts', 'feishu-long-connection-bot.js')],
  },
  doctor: {
    command: 'node',
    args: [path.join('scripts', 'feishu-doctor.js')],
  },
  auth: {
    command: 'python3',
    args: [path.join('plugins', 'feishu', 'scripts', 'feishu-oauth-callback.py')],
  },
  start: {
    command: 'node',
    args: [path.join('scripts', 'feishu-service.js'), 'start'],
  },
  stop: {
    command: 'node',
    args: [path.join('scripts', 'feishu-service.js'), 'stop'],
  },
  restart: {
    command: 'node',
    args: [path.join('scripts', 'feishu-service.js'), 'restart'],
  },
  status: {
    command: 'node',
    args: [path.join('scripts', 'feishu-service.js'), 'status'],
  },
  push: {
    command: 'node',
    args: [path.join('plugins', 'feishu', 'scripts', 'feishu-project-update.js')],
  },
  digest: {
    command: 'node',
    args: [path.join('plugins', 'feishu', 'scripts', 'feishu-daily-digest.js')],
  },
  runner: {
    command: 'node',
    args: [path.join('plugins', 'feishu', 'scripts', 'feishu-codex-runner.js')],
  },
  report: {
    command: 'python3',
    args: [path.join('plugins', 'feishu', 'scripts', 'feishu-project-report.py')],
  },
  webhook: {
    command: 'python3',
    args: [path.join('plugins', 'feishu', 'scripts', 'feishu_webhook_server.py')],
  },
};

function parseArgs(argv) {
  const [command = 'help', ...rest] = argv;
  return {
    command: command === '--help' || command === '-h' ? 'help' : command,
    rest,
  };
}

function resolveInvocation(commandName, extraArgs) {
  const base = COMMANDS[commandName];
  if (!base) {
    return null;
  }
  return {
    command: base.command,
    args: [...base.args, ...extraArgs],
  };
}

function main() {
  const { command, rest } = parseArgs(process.argv.slice(2));
  if (command === 'help') {
    console.log(HELP_TEXT);
    return;
  }

  const invocation = resolveInvocation(command, rest);
  if (!invocation) {
    console.error(`Unknown command: ${command}`);
    console.error('');
    console.error(HELP_TEXT);
    process.exit(1);
  }

  const result = spawnSync(invocation.command, invocation.args, {
    stdio: 'inherit',
    env: process.env,
    cwd: process.cwd(),
    shell: false,
  });

  if (result.error) {
    console.error(result.error.message);
    process.exit(1);
  }

  process.exit(result.status === null ? 1 : result.status);
}

if (require.main === module) {
  main();
}

module.exports = {
  parseArgs,
  resolveInvocation,
};
