#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}/web"
if command -v npm >/dev/null 2>&1; then
  npm ci --no-fund
  npm run build
elif [[ -f "${HOME}/.local/share/npm/bin/npm-cli.js" ]]; then
  node "${HOME}/.local/share/npm/bin/npm-cli.js" ci --no-fund
  node "${HOME}/.local/share/npm/bin/npm-cli.js" run build
else
  echo "需要 Node.js 22.12+ 与 npm。安装后重新运行 scripts/build_web.sh。" >&2
  exit 1
fi
