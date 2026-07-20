#!/usr/bin/env bash
set -euo pipefail

missing=0

if command -v npx >/dev/null 2>&1; then
  echo "ok: npx found at $(command -v npx)"
else
  echo "missing: npx command is not on PATH"
  echo "info: npx is optional when using the stable local HTTP-backed MCP server"
fi

if command -v python3 >/dev/null 2>&1; then
  echo "ok: python3 found at $(command -v python3)"
else
  echo "missing: python3 command is not on PATH"
  missing=1
fi

if [ -n "${FEISHU_APP_ID:-}" ]; then
  echo "ok: app id environment variable is set"
else
  echo "missing: set FEISHU_APP_ID"
  missing=1
fi

if [ -n "${FEISHU_APP_SECRET:-}" ]; then
  echo "ok: app secret environment variable is set"
else
  echo "missing: set FEISHU_APP_SECRET"
  missing=1
fi

if [ -n "${FEISHU_USER_ACCESS_TOKEN:-}" ]; then
  echo "ok: FEISHU_USER_ACCESS_TOKEN is set; user token mode can be used directly"
else
  echo "info: FEISHU_USER_ACCESS_TOKEN is not set; run npm run feishu -- auth, or plugins/feishu/scripts/exchange-feishu-code.sh after browser authorization"
fi

if [ -n "${FEISHU_BOT_OWNER_OPEN_ID:-}" ] || \
  [ -n "${FEISHU_BOT_ADMINS:-}" ] || \
  [ -n "${FEISHU_BOT_ALLOWED_USERS:-}" ] || \
  [ -n "${FEISHU_BOT_ALLOWED_CHATS:-}" ]; then
  echo "ok: bot access control is configured"
else
  echo "missing: configure FEISHU_BOT_OWNER_OPEN_ID or an explicit bot allowlist"
  echo "info: the long-connection bot will not execute local commands without access control"
  missing=2
fi

if [ "$missing" -eq 0 ]; then
  echo "Feishu plugin prerequisites look ready."
else
  echo "Feishu plugin prerequisites are incomplete."
fi

exit "$missing"
