#!/usr/bin/env bash
set -Eeuo pipefail

[[ $# -eq 1 ]] || { printf 'Usage: %s <backup-directory>\n' "$0" >&2; exit 1; }
backup_dir="$1"
[[ -f "$backup_dir/database.dump" ]] || { printf 'database.dump is missing from %s\n' "$backup_dir" >&2; exit 1; }
root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root_dir"
source .env

printf 'This replaces all data in %s. Type RESTORE to continue: ' "$POSTGRES_DB"
read -r confirmation
[[ "$confirmation" == "RESTORE" ]] || { printf 'Restore cancelled.\n'; exit 0; }
docker compose up -d db
docker compose exec -T db pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists < "$backup_dir/database.dump"
if [[ -f "$backup_dir/app_data.tar.gz" ]]; then
  docker run --rm -v "${COMPOSE_PROJECT_NAME:-golden-dome-soc}_app_data:/target" -v "$(cd "$backup_dir" && pwd):/backup:ro" alpine sh -c 'rm -rf /target/* && tar -xzf /backup/app_data.tar.gz -C /target'
fi
printf 'Restore complete. Restart the application with docker compose up -d.\n'
