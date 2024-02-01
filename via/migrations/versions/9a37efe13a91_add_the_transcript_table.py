"""Add the transcript table.

Revision ID: 9a37efe13a91
Revises:
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "9a37efe13a91"
down_revision = None


def upgrade() -> None:
    op.create_table(
        "transcript",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "created", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column(
            "updated", sa.DateTime(), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("video_id", sa.String(), nullable=False),
        sa.Column("transcript_id", sa.String(), nullable=False),
        sa.Column(
            "transcript", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transcript")),
        sa.UniqueConstraint(
            "video_id",
            "transcript_id",
            name=op.f("uq_transcript_video_id_transcript_id"),
        ),
    )


def downgrade() -> None:
    op.drop_table("transcript")
