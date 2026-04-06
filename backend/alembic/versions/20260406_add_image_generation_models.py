"""Add image_generation_models table and assistant toggle

Revision ID: 20260406_image_gen_models
Revises: 20260319_add_nickname, 202411041401
Create Date: 2026-04-06
"""

import sqlalchemy as sa
from alembic import op

revision = "20260406_image_gen_models"
down_revision = ("20260319_add_nickname", "202411041401")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "image_generation_models",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("nickname", sa.String(), nullable=True),
        sa.Column("open_source", sa.Boolean(), nullable=False),
        sa.Column(
            "is_deprecated", sa.Boolean(), server_default="False", nullable=False
        ),
        sa.Column("hf_link", sa.String(), nullable=True),
        sa.Column("family", sa.String(), nullable=False),
        sa.Column("stability", sa.String(), nullable=False),
        sa.Column("hosting", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("org", sa.String(), nullable=True),
        sa.Column("litellm_model_name", sa.String(), nullable=True),
        sa.Column("tenant_id", sa.UUID(), nullable=True, index=True),
        sa.Column("provider_id", sa.UUID(), nullable=True, index=True),
        sa.Column("is_enabled", sa.Boolean(), server_default="True", nullable=False),
        sa.Column(
            "security_classification_id",
            sa.UUID(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["provider_id"], ["model_providers.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["security_classification_id"],
            ["security_classifications.id"],
            ondelete="SET NULL",
        ),
        sa.CheckConstraint(
            "(tenant_id IS NULL AND provider_id IS NULL) OR (tenant_id IS NOT NULL AND provider_id IS NOT NULL)",
            name="ck_image_generation_models_tenant_provider",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.add_column(
        "assistants",
        sa.Column(
            "image_generation_enabled",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("assistants", "image_generation_enabled")
    op.drop_table("image_generation_models")
