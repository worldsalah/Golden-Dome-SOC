#!/usr/bin/env bash
set -Eeuo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root_dir"
port="$(grep '^HTTP_PORT=' .env 2>/dev/null | cut -d= -f2 || true)"
port="${port:-8080}"
failed=0

check_container() {
  local service="$1"
  local state
  state="$(docker compose ps --format json "$service" 2>/dev/null | head -n 1 || true)"
  if [[ "$state" == *'"running"'* ]]; then printf 'PASS  container: %s\n' "$service"; else printf 'FAIL  container: %s\n' "$service"; failed=1; fi
}
check_url() {
  local name="$1" url="$2"
  if curl --fail --silent --max-time 10 "$url" >/dev/null; then printf 'PASS  endpoint: %s\n' "$name"; else printf 'FAIL  endpoint: %s\n' "$name"; failed=1; fi
}

for service in db redis ollama backend frontend gateway; do check_container "$service"; done
check_url gateway "http://localhost:${port}/health"
check_url frontend "http://localhost:${port}/"
check_url backend "http://localhost:${port}/healthz"

if docker compose ps --services --filter status=running | grep -qx wazuh-manager; then
  check_container wazuh-manager
else
  printf 'SKIP  Wazuh profile is not enabled.\n'
fi

if [[ "$failed" -eq 0 ]]; then
  printf '\nVerification succeeded.\n'
else
  printf '\nVerification failed. Inspect logs with: docker compose logs --tail=100\n' >&2
fi
exit "$failed"
