"""Add spaces_image_generation_models junction table

Revision ID: 20260407_spaces_img_gen
Revises: 20260406_image_gen_models
Create Date: 2026-04-07
"""

import sqlalchemy as sa
from alembic import op

revision = "20260407_spaces_img_gen"
down_revision = "20260406_image_gen_models"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "spaces_image_generation_models",
        sa.Column("space_id", sa.Uuid(), nullable=False),
        sa.Column("image_generation_model_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["space_id"], ["spaces.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["image_generation_model_id"],
            ["image_generation_models.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("space_id", "image_generation_model_id"),
    )


def downgrade() -> None:
    op.drop_table("spaces_image_generation_models")
