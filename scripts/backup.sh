#!/usr/bin/env bash
set -Eeuo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root_dir"
source .env
backup_dir="${BACKUP_DIR:-$root_dir/backups}/$(date +%Y%m%dT%H%M%SZ)"
mkdir -p "$backup_dir"

printf 'Backing up PostgreSQL...\n'
docker compose exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom > "$backup_dir/database.dump"
printf 'Backing up configuration and persistent files...\n'
tar --exclude='.env.local' --exclude='.git' -czf "$backup_dir/configuration.tar.gz" .env docker-compose.yml docker-compose.prod.yml nginx scripts docs 2>/dev/null || true
docker run --rm -v "${COMPOSE_PROJECT_NAME:-golden-dome-soc}_app_data:/source:ro" -v "$backup_dir:/backup" alpine sh -c 'tar -czf /backup/app_data.tar.gz -C /source .' 2>/dev/null || true
docker run --rm -v "${COMPOSE_PROJECT_NAME:-golden-dome-soc}_ollama_data:/source:ro" -v "$backup_dir:/backup" alpine sh -c 'tar -czf /backup/ollama_data.tar.gz -C /source .' 2>/dev/null || true
sha256sum "$backup_dir"/* > "$backup_dir/SHA256SUMS"
printf 'Backup created: %s\n' "$backup_dir"
