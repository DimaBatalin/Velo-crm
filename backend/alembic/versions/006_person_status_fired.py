"""add FIRED value to personstatus enum

Revision ID: 006_person_status_fired
Revises: 005_add_roles
Create Date: 2026-07-11
"""
from alembic import op

revision = "006_person_status_fired"
down_revision = "005_add_roles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE нельзя выполнять внутри транзакции,
    # в которой Alembic гоняет миграции — выносим в autocommit.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE personstatus ADD VALUE IF NOT EXISTS 'FIRED'")


def downgrade() -> None:
    # PostgreSQL не умеет удалять значения из enum; откат — no-op.
    # Значение FIRED останется в типе, это безвредно.
    pass
