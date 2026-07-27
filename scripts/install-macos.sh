#!/usr/bin/env bash
set -Eeuo pipefail
if ! command -v docker >/dev/null; then
  printf 'Docker Desktop is required. Install it from https://www.docker.com/products/docker-desktop/ and retry.\n' >&2
  exit 1
fi
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/install.sh"
