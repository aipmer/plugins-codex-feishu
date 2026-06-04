#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

patterns=(
  'cli_[a-z0-9]{16,}'
  'ou_[a-z0-9]{20,}'
  'oc_[a-z0-9]{20,}'
  'om_[a-z0-9]{20,}'
  'FEISHU_APP_SECRET=["'\''][^"'\'']{12,}["'\'']'
  'LARK_APP_SECRET=["'\''][^"'\'']{12,}["'\'']'
)

for pattern in "${patterns[@]}"; do
  if rg -n --hidden \
    --glob '!**/.git/**' \
    --glob '!**/node_modules/**' \
    --glob '!**/.tmp/**' \
    --glob '!tmp/**' \
    --glob '!**/.env' \
    --glob '!**/.env.local' \
    --glob '!**/.env.*.local' \
    "${pattern}" "${REPO_ROOT}" >/tmp/feishu-sensitive-scan.txt; then
    echo "fail: potential real Feishu identifier or secret found for pattern: ${pattern}" >&2
    cat /tmp/feishu-sensitive-scan.txt >&2
    exit 1
  fi
done

echo "ok: no real-looking Feishu app/user/chat/message IDs or secrets found"
