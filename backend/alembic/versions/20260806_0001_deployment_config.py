"""Add deployment_config table for first-launch deployment wizard.

Revision ID: 20260806_0001
Revises: 20260730_0001
"""

from alembic import op
import sqlalchemy as sa

revision = "20260806_0001"
down_revision = "20260730_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS deployment_config (
            id SERIAL PRIMARY KEY,
            installation_name VARCHAR(255) NOT NULL,
            administrator_name VARCHAR(255) NOT NULL,
            company_name VARCHAR(255),
            hostname VARCHAR(255),
            local_ip VARCHAR(64),
            public_ip VARCHAR(64),
            operating_system VARCHAR(255),
            cpu VARCHAR(255),
            ram VARCHAR(64),
            disk VARCHAR(64),
            docker_version VARCHAR(64),
            system_info_snapshot JSON,
            deployment_date TIMESTAMP NOT NULL DEFAULT now(),
            completed BOOLEAN NOT NULL DEFAULT false
        )
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS deployment_config")
