#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${HERMES_NODE_URL:-http://mail.tailb30d36.ts.net:8732}"
TOKEN="${HERMES_NODE_TOKEN_MAIL:-}"

if [[ -z "$TOKEN" ]]; then
  echo "HERMES_NODE_TOKEN_MAIL is required" >&2
  exit 1
fi

curl -fsS \
  -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/health"

echo
