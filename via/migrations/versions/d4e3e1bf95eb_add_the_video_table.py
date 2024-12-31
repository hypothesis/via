"""Add the video table.

Revision ID: d4e3e1bf95eb
Revises:
"""

import sqlalchemy as sa
from alembic import op

revision = "d4e3e1bf95eb"
down_revision = "9a37efe13a91"


def upgrade() -> None:
    op.create_table(
        "video",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("video_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_video")),
        sa.UniqueConstraint("video_id", name=op.f("uq_video_video_id")),
    )


def downgrade() -> None:
    op.drop_table("video")
