import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel


def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)


class MossNote(SQLModel, table=True):
    __tablename__ = "moss_note"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, index=True)
    title: str = Field(default="Untitled note", max_length=255)
    display_title: str | None = Field(default=None, max_length=255)
    preview_text: str = Field(default="")
    canvas_snapshot: str = Field(default="")
    pinned_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    deleted_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    last_opened_conversation_id: uuid.UUID | None = Field(default=None, index=True)
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )
    updated_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )


class MossConversation(SQLModel, table=True):
    __tablename__ = "moss_conversation"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, index=True)
    note_id: uuid.UUID = Field(foreign_key="moss_note.id", nullable=False, index=True)
    title: str = Field(default="Default conversation", max_length=255)
    is_default: bool = Field(default=False)
    pinned_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    deleted_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    created_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )
    updated_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),
    )
