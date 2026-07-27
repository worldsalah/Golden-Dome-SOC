# Production Deployment and Operations

## Production launch

1. Create a protected environment file:

```bash
cp .env.production .env
chmod 600 .env
```

2. Set unique values for `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `SECRET_KEY`, `ADMIN_PASSWORD`, external URLs, and integration credentials.
3. Put TLS termination in front of the gateway (a load balancer, Caddy, or ingress controller). The bundled Nginx gateway intentionally serves HTTP on `HTTP_PORT` and should not be exposed directly to the public internet.
4. Launch the optimized profile:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
./scripts/verify.sh
```

Only the gateway publishes an application port. PostgreSQL, Redis, Ollama, frontend, and backend remain on the private `goldendome` bridge network.

## Upgrades and rollback

```bash
./scripts/backup.sh
docker compose pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
./scripts/verify.sh
```

If an upgrade fails, deploy the previous Git revision or image tag and run `docker compose up -d`. Restore data only when a migration or data change requires it:

```bash
./scripts/restore.sh backups/20260727T120000Z
```

## Scheduled backup

Use cron on the Docker host:

```cron
0 2 * * * /opt/golden-dome-soc/scripts/backup.sh >> /var/log/golden-dome-backup.log 2>&1
```

Protect and encrypt the resulting `backups/` directory before copying it off-host. Test restoration periodically on a non-production environment.

## Security operations

- Store `.env` in a secrets manager for managed deployments and never commit it.
- Rotate the admin password, JWT secret, database, Redis, Wazuh, SMTP, and TI API credentials according to your policy.
- Set `ALLOWED_ORIGINS` and `TRUSTED_HOSTS` to your exact public hostname.
- Publish the gateway only through TLS and limit access with VPN, SSO, or an identity-aware proxy.
- Set `SEED_DEMO_DATA=false` for a production tenant after validating first-start configuration.
- Review logs with `docker compose logs`; Docker rotation is configured at 10 MB × 3 files per service.

## Wazuh operations

The official Wazuh deployment is resource intensive and certificate-based. Bootstrap certificates with the checked-in upstream Wazuh single-node configuration, keep its service credentials in `.env`, and launch `docker compose --profile wazuh up -d`. Reserve at least 8 additional GB RAM and tune `vm.max_map_count` on the host as required by OpenSearch/Wazuh.
