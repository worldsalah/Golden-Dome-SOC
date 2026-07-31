"""Add multi-tenant architecture: organizations, tenant_id on all models, MFA, audit logs, sessions, connectors.

Revision ID: 20260730_0001
Revises: 20260727_0001
"""

from alembic import op
import sqlalchemy as sa

revision = "20260730_0001"
down_revision = "20260727_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # Create organizations table (IF NOT EXISTS because create_all may have already made it)
    op.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            slug VARCHAR(128) UNIQUE NOT NULL,
            industry VARCHAR(128),
            contact_email VARCHAR(128),
            contact_phone VARCHAR(64),
            address TEXT,
            plan VARCHAR(64) NOT NULL DEFAULT 'professional',
            max_users INTEGER NOT NULL DEFAULT 50,
            max_assets INTEGER NOT NULL DEFAULT 500,
            is_active BOOLEAN NOT NULL DEFAULT true,
            settings JSON,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_organizations_name ON organizations(name)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_organizations_slug ON organizations(slug)")

    # Add columns to users (IF NOT EXISTS for idempotency)
    user_cols = [
        ("organization_id", "INTEGER REFERENCES organizations(id)"),
        ("mfa_secret", "VARCHAR(255)"),
        ("mfa_enabled", "BOOLEAN NOT NULL DEFAULT false"),
        ("mfa_backup_codes", "TEXT"),
        ("last_login", "TIMESTAMP"),
        ("last_login_ip", "VARCHAR(64)"),
        ("failed_login_count", "INTEGER NOT NULL DEFAULT 0"),
        ("password_changed_at", "TIMESTAMP"),
    ]
    for col, dtype in user_cols:
        op.execute(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} {dtype}")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_organization_id ON users(organization_id)")

    # Migrate existing roles
    op.execute("UPDATE users SET role = 'super_admin' WHERE role = 'admin'")
    op.execute("UPDATE users SET role = 'analyst' WHERE role = 'soc_analyst'")
    op.execute("UPDATE users SET role = 'executive' WHERE role = 'viewer'")

    # Add tenant_id to all tenant-scoped tables
    tenant_tables = [
        "assets", "alerts", "incidents", "asset_vulnerabilities",
        "threat_intelligence", "ioc_database", "ai_analysis",
        "risk_scores", "detection_rules", "reports", "playbooks",
        "threat_iocs", "vulnerability_intelligence",
    ]
    for table in tenant_tables:
        op.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS tenant_id INTEGER REFERENCES organizations(id)")
        op.execute(f"CREATE INDEX IF NOT EXISTS ix_{table}_tenant_id ON {table}(tenant_id)")

    # Drop unique constraints and create non-unique indexes
    op.execute("ALTER TABLE assets DROP CONSTRAINT IF EXISTS assets_wazuh_agent_id_key")
    op.execute("CREATE INDEX IF NOT EXISTS ix_assets_wazuh_agent_id ON assets(wazuh_agent_id)")
    op.execute("ALTER TABLE alerts DROP CONSTRAINT IF EXISTS alerts_wazuh_alert_id_key")
    op.execute("CREATE INDEX IF NOT EXISTS ix_alerts_wazuh_alert_id ON alerts(wazuh_alert_id)")
    op.execute("ALTER TABLE vulnerability_intelligence DROP CONSTRAINT IF EXISTS vulnerability_intelligence_cve_key")

    # Create audit_logs table
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id SERIAL PRIMARY KEY,
            tenant_id INTEGER REFERENCES organizations(id),
            user_id INTEGER REFERENCES users(id),
            username VARCHAR(64),
            action VARCHAR(128) NOT NULL,
            resource_type VARCHAR(64),
            resource_id VARCHAR(64),
            ip_address VARCHAR(64),
            user_agent TEXT,
            details TEXT,
            status VARCHAR(32) NOT NULL DEFAULT 'success',
            created_at TIMESTAMP NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_tenant_id ON audit_logs(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_user_id ON audit_logs(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs(created_at)")

    # Create user_sessions table
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            tenant_id INTEGER REFERENCES organizations(id),
            token_jti VARCHAR(128),
            ip_address VARCHAR(64),
            user_agent TEXT,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            expires_at TIMESTAMP,
            revoked_at TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_sessions_user_id ON user_sessions(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_sessions_tenant_id ON user_sessions(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_sessions_token_jti ON user_sessions(token_jti)")

    # Create connectors table
    op.execute("""
        CREATE TABLE IF NOT EXISTS connectors (
            id SERIAL PRIMARY KEY,
            tenant_id INTEGER REFERENCES organizations(id),
            name VARCHAR(128) NOT NULL,
            connector_type VARCHAR(64) NOT NULL,
            category VARCHAR(64) NOT NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'disconnected',
            config TEXT DEFAULT '{}',
            credentials TEXT,
            last_connected TIMESTAMP,
            last_sync TIMESTAMP,
            health_status VARCHAR(32) NOT NULL DEFAULT 'unknown',
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_connectors_tenant_id ON connectors(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_connectors_connector_type ON connectors(connector_type)")

    # Create connector_logs table
    op.execute("""
        CREATE TABLE IF NOT EXISTS connector_logs (
            id SERIAL PRIMARY KEY,
            connector_id INTEGER NOT NULL REFERENCES connectors(id),
            level VARCHAR(32) NOT NULL DEFAULT 'info',
            message TEXT NOT NULL,
            details TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_connector_logs_connector_id ON connector_logs(connector_id)")

    # Create api_keys table
    op.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id SERIAL PRIMARY KEY,
            tenant_id INTEGER REFERENCES organizations(id),
            name VARCHAR(128) NOT NULL,
            key_hash VARCHAR(128) NOT NULL UNIQUE,
            key_prefix VARCHAR(16) NOT NULL,
            scopes TEXT NOT NULL DEFAULT '[]',
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_by INTEGER REFERENCES users(id),
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            revoked_at TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_api_keys_tenant_id ON api_keys(tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_api_keys_key_hash ON api_keys(key_hash)")


def downgrade() -> None:
    op.drop_table("api_keys")
    op.drop_table("connector_logs")
    op.drop_table("connectors")
    op.drop_table("user_sessions")
    op.drop_table("audit_logs")

    tenant_tables = [
        "vulnerability_intelligence", "threat_iocs", "playbooks",
        "reports", "detection_rules", "risk_scores", "ai_analysis",
        "ioc_database", "threat_intelligence", "asset_vulnerabilities",
        "incidents", "alerts", "assets",
    ]
    for table in tenant_tables:
        op.drop_column(table, "tenant_id")

    op.drop_column("users", "password_changed_at")
    op.drop_column("users", "failed_login_count")
    op.drop_column("users", "last_login_ip")
    op.drop_column("users", "last_login")
    op.drop_column("users", "mfa_backup_codes")
    op.drop_column("users", "mfa_enabled")
    op.drop_column("users", "mfa_secret")
    op.drop_column("users", "organization_id")

    op.drop_table("organizations")
