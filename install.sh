#!/usr/bin/env bash
# Golden Dome SOC Appliance Installer
# Run on a fresh Ubuntu/Debian server as root or with sudo.
set -Eeuo pipefail

INSTALL_DIR="${INSTALL_DIR:-/opt/goldendome}"
REPO_URL="https://github.com/worldsalah/Golden-Dome-SOC.git"
CURRENT_USER="$(id -un 2>/dev/null || true)"

fail() { printf '\n[ERROR] %s\n' "$1" >&2; exit 1; }
ok() { printf '[OK] %s\n' "$1"; }

# ------------------------------------------------------------------
# Requirements
# ------------------------------------------------------------------
if [[ "$EUID" -ne 0 && -z "${SKIP_SUDO:-}" ]]; then
  command -v sudo >/dev/null || fail "Run as root or with sudo available."
fi

if ! command -v curl >/dev/null && ! command -v wget >/dev/null; then
  fail "curl or wget is required."
fi

if ! command -v docker >/dev/null; then
  ok "Docker not found. Installing Docker Engine..."
  if command -v apt-get >/dev/null; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y -qq ca-certificates curl gnupg
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  elif command -v dnf >/dev/null; then
    dnf -y install dnf-plugins-core
    dnf config-manager --add-repo https://download.docker.com/linux/rhel/docker-ce.repo || true
    dnf -y install docker-ce docker-ce-cli containerd.io docker-compose-plugin
  elif command -v yum >/dev/null; then
    yum -y install yum-utils
    yum-config-manager --add-repo https://download.docker.com/linux/rhel/docker-ce.repo || true
    yum -y install docker-ce docker-ce-cli containerd.io docker-compose-plugin
  else
    fail "Could not install Docker: no supported package manager (apt, dnf, yum)."
  fi

  systemctl enable --now docker || true
  usermod -aG docker "${SUDO_USER:-$CURRENT_USER}" 2>/dev/null || true
fi

if ! docker compose version >/dev/null 2>&1; then
  fail "Docker Compose v2 is required. Please install it and re-run."
fi

# ------------------------------------------------------------------
# Install files
# ------------------------------------------------------------------
if [[ -d "$INSTALL_DIR/.git" ]]; then
  ok "Golden Dome already installed at $INSTALL_DIR. Updating..."
  (cd "$INSTALL_DIR" && git pull --ff-only)
else
  if [[ -d "$INSTALL_DIR" ]]; then
    fail "Install directory $INSTALL_DIR exists but is not a git clone. Remove it or set INSTALL_DIR."
  fi
  ok "Cloning Golden Dome to $INSTALL_DIR..."
  git clone "$REPO_URL" "$INSTALL_DIR" --depth 1
fi

cd "$INSTALL_DIR"

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
SERVER_IP="${SERVER_IP:-$(ip route get 1.1.1.1 2>/dev/null | head -1 | sed -n 's/.*src \([0-9.]*\).*/\1/p' || hostname -I | awk '{print $1}')}"
SERVER_IP="${SERVER_IP:-127.0.0.1}"

if [[ ! -f .env ]]; then
  cp production.env .env
  SECRET_KEY="$(openssl rand -hex 32 2>/dev/null || date +%s | sha256sum | cut -d' ' -f1)"
  POSTGRES_PASSWORD="$(openssl rand -hex 24 2>/dev/null || date +%s | sha256sum | cut -d' ' -f1)"
  REDIS_PASSWORD="$(openssl rand -hex 24 2>/dev/null || date +%s | sha256sum | cut -d' ' -f1)"
  sed -i \
    -e "s|^SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" \
    -e "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$POSTGRES_PASSWORD|" \
    -e "s|^REDIS_PASSWORD=.*|REDIS_PASSWORD=$REDIS_PASSWORD|" \
    -e "s|^GOLDENDOME_HOSTNAME=.*|GOLDENDOME_HOSTNAME=$SERVER_IP|" \
    .env
  ok "Generated .env with random secrets."
fi

mkdir -p certs backups logs

# ------------------------------------------------------------------
# TLS certificates
# ------------------------------------------------------------------
if [[ ! -f certs/goldendome.crt || ! -f certs/goldendome.key ]]; then
  ok "Generating self-signed TLS certificates..."
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout certs/goldendome.key \
    -out certs/goldendome.crt \
    -subj "/CN=${SERVER_IP}/O=Golden Dome/C=US" \
    -addext "subjectAltName = IP:${SERVER_IP},DNS:goldendome.local" 2>/dev/null || \
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout certs/goldendome.key \
    -out certs/goldendome.crt \
    -subj "/CN=${SERVER_IP}/O=Golden Dome/C=US"
  chmod 600 certs/goldendome.key
  ok "Self-signed certificate created. Replace certs/goldendome.crt and certs/goldendome.key to use your own certificate."
else
  ok "Using existing TLS certificates."
fi

# ------------------------------------------------------------------
# Start appliance
# ------------------------------------------------------------------
ok "Pulling and building production images..."
docker compose -f docker-compose.production.yml pull
docker compose -f docker-compose.production.yml build

ok "Starting Golden Dome appliance..."
docker compose -f docker-compose.production.yml up -d

ok "Waiting for platform to become healthy (this may take a minute)..."
for i in {1..60}; do
  if curl -skf "https://${SERVER_IP}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

if curl -skf "https://${SERVER_IP}/health" >/dev/null 2>&1; then
  ok "Gateway is healthy."
else
  fail "Gateway did not become healthy. Check logs: docker compose -f docker-compose.production.yml logs"
fi

if ! curl -skf "https://${SERVER_IP}/api/health" >/dev/null 2>&1; then
  ok "Backend is starting (first boot may take longer)."
fi

# ------------------------------------------------------------------
# Auto-start after reboot
# ------------------------------------------------------------------
if command -v systemctl >/dev/null; then
  SYSTEMD_DIR="/etc/systemd/system"
  cat > "${SYSTEMD_DIR}/goldendome-appliance.service" <<EOF
[Unit]
Description=Golden Dome SOC Appliance
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=${INSTALL_DIR}
ExecStart=/usr/bin/docker compose -f docker-compose.production.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose.production.yml down
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
EOF
  systemctl daemon-reload
  systemctl enable --now goldendome-appliance.service || true
  ok "Enabled systemd service for automatic startup after reboot."
fi

# ------------------------------------------------------------------
# Done
# ------------------------------------------------------------------
cat <<EOF

============================================================
  Golden Dome installed successfully.
============================================================

Access the platform:
  https://${SERVER_IP}

Installation directory:
  ${INSTALL_DIR}

Self-signed certificate generated for ${SERVER_IP}.
To use your own certificate, replace:
  ${INSTALL_DIR}/certs/goldendome.crt
  ${INSTALL_DIR}/certs/goldendome.key

Management commands:
  cd ${INSTALL_DIR}
  docker compose -f docker-compose.production.yml logs -f
  docker compose -f docker-compose.production.yml ps

Backups:
  Backups are written to ${INSTALL_DIR}/backups.
  Run docker compose -f docker-compose.production.yml --profile backup up -d
  to enable automatic daily backups.

On first access, the setup wizard will appear.
EOF
