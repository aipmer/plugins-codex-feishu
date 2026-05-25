#!/usr/bin/env node
require('dotenv').config({ quiet: true });

const { spawnSync } = require('child_process');
const path = require('path');

const scriptPath = path.join(__dirname, '..', 'plugins', 'feishu', 'scripts', 'doctor-feishu-auth.sh');
const result = spawnSync(scriptPath, {
  stdio: 'inherit',
  env: process.env,
  shell: false,
});

if (result.error) {
  console.error(result.error.message);
  process.exit(1);
}

process.exit(result.status === null ? 1 : result.status);
