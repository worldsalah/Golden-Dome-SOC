#!/usr/bin/env bash
set -Eeuo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root_dir"

fail() { printf '\nERROR: %s\n' "$1" >&2; exit 1; }
command -v docker >/dev/null || fail "Docker is required. Install Docker Engine/Desktop and retry."
docker compose version >/dev/null 2>&1 || fail "Docker Compose v2 is required."

if [[ ! -f .env ]]; then
  cp .env.example .env
  secret="$(openssl rand -hex 32 2>/dev/null || date +%s | sha256sum | cut -d' ' -f1)"
  db_password="$(openssl rand -hex 24 2>/dev/null || date +%s | sha256sum | cut -d' ' -f1)"
  redis_password="$(openssl rand -hex 24 2>/dev/null || date +%s | sha256sum | cut -d' ' -f1)"
  sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$secret|; s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$db_password|; s|^REDIS_PASSWORD=.*|REDIS_PASSWORD=$redis_password|" .env
  printf 'Created .env with generated local secrets. Update ADMIN_PASSWORD before an internet-facing deployment.\n'
fi

mkdir -p backups logs
printf 'Pulling and building platform images...\n'
docker compose pull
docker compose build
docker compose up -d
"$root_dir/scripts/verify.sh"
printf '\nGolden Dome SOC is available at http://localhost:%s\n' "$(grep '^HTTP_PORT=' .env | cut -d= -f2 || echo 8080)"
printf 'Log in using ADMIN_USERNAME and ADMIN_PASSWORD from .env.\n'
