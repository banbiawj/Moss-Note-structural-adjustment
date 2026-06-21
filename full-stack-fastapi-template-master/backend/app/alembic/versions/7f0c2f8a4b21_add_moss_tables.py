"""Add Moss note and conversation tables

Revision ID: 7f0c2f8a4b21
Revises: fe56fa70289e
Create Date: 2026-06-21 19:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = "7f0c2f8a4b21"
down_revision = "fe56fa70289e"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "moss_note",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("display_title", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column("preview_text", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("canvas_snapshot", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("pinned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_opened_conversation_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_moss_note_owner_id"), "moss_note", ["owner_id"], unique=False)
    op.create_index(
        op.f("ix_moss_note_last_opened_conversation_id"),
        "moss_note",
        ["last_opened_conversation_id"],
        unique=False,
    )
    op.create_table(
        "moss_conversation",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("note_id", sa.Uuid(), nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("pinned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["note_id"], ["moss_note.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_moss_conversation_note_id"),
        "moss_conversation",
        ["note_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_moss_conversation_owner_id"),
        "moss_conversation",
        ["owner_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_moss_conversation_owner_id"), table_name="moss_conversation")
    op.drop_index(op.f("ix_moss_conversation_note_id"), table_name="moss_conversation")
    op.drop_table("moss_conversation")
    op.drop_index(op.f("ix_moss_note_last_opened_conversation_id"), table_name="moss_note")
    op.drop_index(op.f("ix_moss_note_owner_id"), table_name="moss_note")
    op.drop_table("moss_note")
