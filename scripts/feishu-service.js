#!/usr/bin/env node
require('dotenv').config({ quiet: true });

const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const DEFAULT_STATE_DIR = path.join(os.homedir(), '.codex-feishu', 'state');
const DEFAULT_SERVICE_LABEL = 'com.hunkwu.feishu-codex.bot';

function getRepoRoot() {
  return path.resolve(__dirname, '..');
}

function getBotStateDir() {
  return path.resolve((process.env.FEISHU_BOT_STATE_DIR || DEFAULT_STATE_DIR).trim() || DEFAULT_STATE_DIR);
}

function getServiceDir() {
  return path.join(getBotStateDir(), 'service');
}

function getServiceConfig() {
  const serviceDir = getServiceDir();
  const label = (process.env.FEISHU_SERVICE_LABEL || DEFAULT_SERVICE_LABEL).trim() || DEFAULT_SERVICE_LABEL;
  const stdoutLog = path.resolve((process.env.FEISHU_SERVICE_STDOUT_LOG || path.join(serviceDir, 'stdout.log')).trim());
  const stderrLog = path.resolve((process.env.FEISHU_SERVICE_STDERR_LOG || path.join(serviceDir, 'stderr.log')).trim());
  const plistPath = path.join(serviceDir, 'launchd.plist');
  const serviceJsonPath = path.join(serviceDir, 'service.json');
  return {
    label,
    mode: 'launchd',
    repoRoot: getRepoRoot(),
    stateDir: getBotStateDir(),
    serviceDir,
    plistPath,
    serviceJsonPath,
    stdoutLog,
    stderrLog,
    botScriptPath: path.join(getRepoRoot(), 'plugins', 'feishu', 'scripts', 'feishu-long-connection-bot.js'),
    nodePath: process.execPath,
    launchctlDomain: `gui/${typeof process.getuid === 'function' ? process.getuid() : '0'}`,
  };
}

function getLaunchctlTarget(config) {
  return `${config.launchctlDomain}/${config.label}`;
}

function ensureServiceDirs(config) {
  fs.mkdirSync(config.serviceDir, { recursive: true });
  fs.closeSync(fs.openSync(config.stdoutLog, 'a'));
  fs.closeSync(fs.openSync(config.stderrLog, 'a'));
}

function buildEnvironmentVariables() {
  const allowed = {};
  for (const [key, value] of Object.entries(process.env)) {
    if (typeof value !== 'string') {
      continue;
    }
    if (key.startsWith('FEISHU_') || ['PATH', 'HOME', 'SHELL', 'LANG', 'LC_ALL', 'LC_CTYPE', 'USER'].includes(key)) {
      allowed[key] = value;
    }
  }
  return allowed;
}

function xmlEscape(value) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&apos;');
}

function buildLaunchdPlist(config) {
  const envXml = Object.entries(buildEnvironmentVariables())
    .map(([key, value]) => `    <key>${xmlEscape(key)}</key>\n    <string>${xmlEscape(value)}</string>`)
    .join('\n');

  return `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${xmlEscape(config.label)}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${xmlEscape(config.nodePath)}</string>
    <string>${xmlEscape(config.botScriptPath)}</string>
  </array>
  <key>WorkingDirectory</key>
  <string>${xmlEscape(config.repoRoot)}</string>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>${xmlEscape(config.stdoutLog)}</string>
  <key>StandardErrorPath</key>
  <string>${xmlEscape(config.stderrLog)}</string>
  <key>EnvironmentVariables</key>
  <dict>
${envXml}
  </dict>
</dict>
</plist>
`;
}

function readServiceMetadata(config) {
  if (!fs.existsSync(config.serviceJsonPath)) {
    return null;
  }
  return JSON.parse(fs.readFileSync(config.serviceJsonPath, 'utf8'));
}

function writeServiceMetadata(config, patch = {}) {
  ensureServiceDirs(config);
  const previous = readServiceMetadata(config) || {};
  const next = {
    label: config.label,
    mode: config.mode,
    state_dir: config.stateDir,
    stdout_log: config.stdoutLog,
    stderr_log: config.stderrLog,
    plist_path: config.plistPath,
    ...previous,
    ...patch,
  };
  fs.writeFileSync(config.serviceJsonPath, `${JSON.stringify(next, null, 2)}\n`, 'utf8');
  return next;
}

function writeLaunchdConfig(config) {
  ensureServiceDirs(config);
  fs.writeFileSync(config.plistPath, buildLaunchdPlist(config), 'utf8');
  return writeServiceMetadata(config);
}

function clearBotRunState(stateDir) {
  for (const entry of fs.readdirSync(stateDir, { withFileTypes: true })) {
    if (!entry.isFile() || !entry.name.endsWith('.json')) {
      continue;
    }
    const filePath = path.join(stateDir, entry.name);
    const raw = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    const queued = Array.isArray(raw.queuedMessages) ? raw.queuedMessages : [];
    const next = {
      ...raw,
      running: false,
      currentPid: null,
      currentRunId: '',
      currentStartedAt: '',
      stopRequested: false,
      status: queued.length ? 'queued' : (raw.status === 'cancelling' ? 'cancelled' : (raw.status === 'running' ? 'idle' : raw.status)),
    };
    fs.writeFileSync(filePath, `${JSON.stringify(next, null, 2)}\n`, 'utf8');
  }
}

function isMacOS() {
  return process.platform === 'darwin';
}

function isLaunchctlAvailable() {
  if (!isMacOS()) {
    return false;
  }
  const result = spawnSync('launchctl', ['help'], {
    stdio: 'ignore',
    shell: false,
  });
  return !result.error && result.status === 0;
}

function runLaunchctl(args, inherit = false) {
  return spawnSync('launchctl', args, {
    stdio: inherit ? 'inherit' : 'pipe',
    shell: false,
    encoding: 'utf8',
  });
}

function ensureSupportedEnvironment(config) {
  if (!isMacOS()) {
    throw new Error('Service management is only supported on macOS in this version.');
  }
  if (!isLaunchctlAvailable()) {
    throw new Error('launchctl is not available on this machine.');
  }
  ensureServiceDirs(config);
}

function parseLaunchctlPrint(text) {
  const stateMatch = text.match(/state = ([^\n]+)/);
  const pidMatch = text.match(/\bpid = (\d+)/);
  return {
    state: stateMatch ? stateMatch[1].trim() : 'unknown',
    pid: pidMatch ? pidMatch[1].trim() : '',
  };
}

function formatServiceStatus(summary) {
  return [
    `Service label: ${summary.label}`,
    `Mode: ${summary.mode}`,
    `Platform supported: ${summary.platformSupported ? 'yes' : 'no'}`,
    `Launchctl available: ${summary.launchctlAvailable ? 'yes' : 'no'}`,
    `Launchctl loaded: ${summary.loaded ? 'yes' : 'no'}`,
    `Launchctl state: ${summary.launchctlState || 'unknown'}`,
    `PID: ${summary.pid || 'none'}`,
    `State dir: ${summary.stateDir}`,
    `Stdout log: ${summary.stdoutLog}`,
    `Stderr log: ${summary.stderrLog}`,
    `Plist path: ${summary.plistPath}`,
    `Last started: ${summary.lastStartedAt || 'never'}`,
    `Last stopped: ${summary.lastStoppedAt || 'never'}`,
  ].join('\n');
}

function getServiceStatus(config = getServiceConfig()) {
  const metadata = readServiceMetadata(config) || {};
  const summary = {
    label: config.label,
    mode: config.mode,
    platformSupported: isMacOS(),
    launchctlAvailable: isLaunchctlAvailable(),
    loaded: false,
    launchctlState: 'not_loaded',
    pid: '',
    stateDir: config.stateDir,
    stdoutLog: config.stdoutLog,
    stderrLog: config.stderrLog,
    plistPath: config.plistPath,
    lastStartedAt: metadata.last_started_at || '',
    lastStoppedAt: metadata.last_stopped_at || '',
  };

  if (!summary.platformSupported || !summary.launchctlAvailable) {
    return summary;
  }

  const result = runLaunchctl(['print', getLaunchctlTarget(config)], false);
  if (result.status === 0) {
    const parsed = parseLaunchctlPrint(result.stdout || '');
    summary.loaded = true;
    summary.launchctlState = parsed.state;
    summary.pid = parsed.pid;
  }

  return summary;
}

function startService(config = getServiceConfig()) {
  ensureSupportedEnvironment(config);
  writeLaunchdConfig(config);
  const target = getLaunchctlTarget(config);

  let bootstrap = runLaunchctl(['bootstrap', config.launchctlDomain, config.plistPath], false);
  if (bootstrap.status !== 0) {
    runLaunchctl(['bootout', target], false);
    bootstrap = runLaunchctl(['bootstrap', config.launchctlDomain, config.plistPath], false);
  }
  if (bootstrap.status !== 0) {
    throw new Error((bootstrap.stderr || bootstrap.stdout || 'launchctl bootstrap failed').trim());
  }

  const kickstart = runLaunchctl(['kickstart', '-k', target], false);
  if (kickstart.status !== 0) {
    throw new Error((kickstart.stderr || kickstart.stdout || 'launchctl kickstart failed').trim());
  }

  writeServiceMetadata(config, {
    last_started_at: new Date().toISOString(),
  });
  return getServiceStatus(config);
}

function stopService(config = getServiceConfig()) {
  ensureSupportedEnvironment(config);
  const target = getLaunchctlTarget(config);
  const result = runLaunchctl(['bootout', target], false);
  const errorText = (result.stderr || result.stdout || '').trim();
  if (result.status !== 0 && !/Could not find service|No such process|not found/i.test(errorText)) {
    throw new Error(errorText || 'launchctl bootout failed');
  }

  clearBotRunState(config.stateDir);
  writeServiceMetadata(config, {
    last_stopped_at: new Date().toISOString(),
  });
  return getServiceStatus(config);
}

function restartService(config = getServiceConfig()) {
  stopService(config);
  return startService(config);
}

function printServiceEnvironmentCheck(config = getServiceConfig()) {
  ensureServiceDirs(config);
  console.log('Service precheck:');
  console.log(`- macOS: ${isMacOS() ? 'yes' : 'no'}`);
  console.log(`- launchctl: ${isLaunchctlAvailable() ? 'available' : 'missing'}`);
  console.log(`- state dir writable: yes (${config.stateDir})`);
}

function parseArgs(argv) {
  const [command = 'help'] = argv;
  return { command };
}

function usage() {
  return `Usage:
  node scripts/feishu-service.js <command>

Commands:
  start
  stop
  restart
  status
  help
`;
}

function main() {
  const { command } = parseArgs(process.argv.slice(2));
  if (command === 'help' || command === '--help' || command === '-h') {
    console.log(usage());
    return;
  }

  const config = getServiceConfig();
  let summary;
  if (command === 'start') {
    summary = startService(config);
  } else if (command === 'stop') {
    summary = stopService(config);
  } else if (command === 'restart') {
    summary = restartService(config);
  } else if (command === 'status') {
    summary = getServiceStatus(config);
  } else {
    throw new Error(`Unknown service command: ${command}`);
  }

  console.log(formatServiceStatus(summary));
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
  buildLaunchdPlist,
  clearBotRunState,
  formatServiceStatus,
  getBotStateDir,
  getLaunchctlTarget,
  getServiceConfig,
  getServiceDir,
  getServiceStatus,
  isLaunchctlAvailable,
  isMacOS,
  parseArgs,
  printServiceEnvironmentCheck,
  readServiceMetadata,
  restartService,
  startService,
  stopService,
  usage,
  writeLaunchdConfig,
  writeServiceMetadata,
};
