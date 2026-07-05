"""add user role and created_by_user_id

Revision ID: 005_add_roles
Revises: 004_add_tags
Create Date: 2026-07-05
"""
from alembic import op
import sqlalchemy as sa

revision = "005_add_roles"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


user_role_enum = sa.Enum("ADMIN", "MECHANIC", "MANAGER", name="userrole")


def upgrade() -> None:
    user_role_enum.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "users",
        sa.Column(
            "role",
            user_role_enum,
            nullable=False,
            server_default="MECHANIC",
        ),
    )

    # Первый (уже существующий) пользователь должен стать admin —
    # иначе после этой миграции им некому будет управлять системой.
    op.execute("UPDATE users SET role = 'ADMIN' WHERE id = (SELECT MIN(id) FROM users)")

    op.add_column(
        "repairs",
        sa.Column(
            "created_by_user_id",
            sa.Integer(),
            nullable=True,
            comment="Сотрудник, создавший запись о ремонте",
        ),
    )
    op.create_foreign_key(
        "fk_repairs_created_by_user_id_users",
        "repairs", "users",
        ["created_by_user_id"], ["id"],
    )

    op.add_column(
        "rentals",
        sa.Column(
            "created_by_user_id",
            sa.Integer(),
            nullable=True,
            comment="Сотрудник, создавший запись об аренде",
        ),
    )
    op.create_foreign_key(
        "fk_rentals_created_by_user_id_users",
        "rentals", "users",
        ["created_by_user_id"], ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_rentals_created_by_user_id_users", "rentals", type_="foreignkey")
    op.drop_column("rentals", "created_by_user_id")

    op.drop_constraint("fk_repairs_created_by_user_id_users", "repairs", type_="foreignkey")
    op.drop_column("repairs", "created_by_user_id")

    op.drop_column("users", "role")
    user_role_enum.drop(op.get_bind(), checkfirst=True)
