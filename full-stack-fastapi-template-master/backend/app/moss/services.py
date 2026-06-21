from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from uuid import UUID

from sqlmodel import Session, col, select

from app.moss.models import MossConversation, MossNote
from app.moss.schemas import (
    MossConversationListResponse,
    MossConversationMessagesResponse,
    MossConversationSummary,
    MossCreateConversationResponse,
    MossDeleteConversationResponse,
    MossDeleteNoteResponse,
    MossNoteDetail,
    MossNoteListResponse,
    MossNoteSummary,
    MossUpdateNoteResponse,
)


DEFAULT_NOTE_TITLE = "Untitled note"
DEFAULT_NOTE_CONVERSATION_TITLE = "Default conversation"
DEFAULT_NEW_CONVERSATION_TITLE = "New discussion"
_UNSET = object()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_text(text: str) -> str:
    normalized = re.sub(r"\s+", " ", html.unescape(text)).strip()
    return re.sub(r"\s+([,.;:!?])", r"\1", normalized)


def truncate_preview(text: str) -> str:
    return normalize_text(text)[:240]


@dataclass(frozen=True)
class NoteMetadata:
    title: str
    preview_text: str


class _NoteHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.text_parts: list[str] = []
        self.heading_parts: list[str] = []
        self._heading_depth = 0
        self._capturing_first_heading = False
        self._has_completed_first_heading = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if re.fullmatch(r"h[1-6]", tag.lower()):
            self._heading_depth += 1
            if not self._has_completed_first_heading:
                self._capturing_first_heading = True

    def handle_endtag(self, tag: str) -> None:
        if re.fullmatch(r"h[1-6]", tag.lower()) and self._heading_depth > 0:
            self._heading_depth -= 1
            if self._capturing_first_heading and self._heading_depth == 0:
                self._capturing_first_heading = False
                self._has_completed_first_heading = True

    def handle_data(self, data: str) -> None:
        self.text_parts.append(data)
        if self._capturing_first_heading:
            self.heading_parts.append(data)


def extract_note_metadata(canvas_snapshot: str) -> NoteMetadata:
    parser = _NoteHtmlParser()
    parser.feed(canvas_snapshot)
    parser.close()

    plain_text = normalize_text(" ".join(parser.text_parts))
    heading_text = normalize_text(" ".join(parser.heading_parts))
    title = heading_text or plain_text or DEFAULT_NOTE_TITLE
    return NoteMetadata(title=title, preview_text=truncate_preview(plain_text))


def _note_summary_from_row(
    note: MossNote,
    default_conversation_id: UUID,
    active_conversation_id: UUID,
) -> MossNoteSummary:
    title = note.display_title or note.title
    return MossNoteSummary(
        note_id=note.id,
        default_conversation_id=default_conversation_id,
        active_conversation_id=active_conversation_id,
        title=note.title,
        display_title=note.display_title,
        effective_title=title,
        preview_text=note.preview_text,
        pinned_at=note.pinned_at,
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


def _note_detail_from_row(
    note: MossNote,
    default_conversation_id: UUID,
    active_conversation_id: UUID,
) -> MossNoteDetail:
    summary = _note_summary_from_row(
        note,
        default_conversation_id=default_conversation_id,
        active_conversation_id=active_conversation_id,
    )
    return MossNoteDetail(
        **summary.model_dump(),
        canvas_snapshot=note.canvas_snapshot,
        last_opened_conversation_id=note.last_opened_conversation_id,
    )


def _conversation_summary_from_row(conversation: MossConversation) -> MossConversationSummary:
    return MossConversationSummary(
        conversation_id=conversation.id,
        note_id=conversation.note_id,
        title=conversation.title,
        is_default=conversation.is_default,
        pinned_at=conversation.pinned_at,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


def _conversation_messages_empty() -> MossConversationMessagesResponse:
    return MossConversationMessagesResponse(messages=[])


def _require_note(session: Session, owner_id: UUID, note_id: UUID) -> MossNote:
    note = session.get(MossNote, note_id)
    if note is None or note.owner_id != owner_id or note.deleted_at is not None:
        raise KeyError(f"note not found: {note_id}")
    return note


def _require_conversation(
    session: Session,
    owner_id: UUID,
    note_id: UUID,
    conversation_id: UUID,
) -> MossConversation:
    conversation = session.get(MossConversation, conversation_id)
    if (
        conversation is None
        or conversation.owner_id != owner_id
        or conversation.note_id != note_id
        or conversation.deleted_at is not None
    ):
        raise KeyError(f"conversation not found: {conversation_id}")
    return conversation


def _active_conversation_id(note: MossNote, default_conversation_id: UUID) -> UUID:
    if note.last_opened_conversation_id is not None:
        return note.last_opened_conversation_id
    return default_conversation_id


def list_notes(session: Session, owner_id: UUID) -> MossNoteListResponse:
    statement = (
        select(MossNote)
        .where(MossNote.owner_id == owner_id, col(MossNote.deleted_at).is_(None))
        .order_by(
            col(MossNote.pinned_at).is_(None).asc(),
            col(MossNote.pinned_at).desc(),
            col(MossNote.updated_at).desc(),
        )
    )
    notes = session.exec(statement).all()
    summaries: list[MossNoteSummary] = []
    for note in notes:
        default_conversation = session.exec(
            select(MossConversation).where(
                MossConversation.note_id == note.id,
                col(MossConversation.is_default).is_(True),
                col(MossConversation.deleted_at).is_(None),
            )
        ).first()
        if default_conversation is None:
            continue
        summaries.append(
            _note_summary_from_row(
                note,
                default_conversation_id=default_conversation.id,
                active_conversation_id=_active_conversation_id(note, default_conversation.id),
            )
        )
    return MossNoteListResponse(notes=summaries)


def create_note(session: Session, owner_id: UUID) -> MossNoteDetail:
    now = utc_now()
    note = MossNote(owner_id=owner_id, created_at=now, updated_at=now)
    conversation = MossConversation(
        owner_id=owner_id,
        note_id=note.id,
        title=DEFAULT_NOTE_CONVERSATION_TITLE,
        is_default=True,
        created_at=now,
        updated_at=now,
    )
    session.add(note)
    session.add(conversation)
    session.commit()
    session.refresh(note)
    session.refresh(conversation)
    return _note_detail_from_row(
        note,
        default_conversation_id=conversation.id,
        active_conversation_id=conversation.id,
    )


def get_note(session: Session, owner_id: UUID, note_id: UUID) -> MossNoteDetail:
    note = _require_note(session, owner_id, note_id)
    default_conversation = session.exec(
        select(MossConversation).where(
            MossConversation.note_id == note.id,
            col(MossConversation.is_default).is_(True),
            col(MossConversation.deleted_at).is_(None),
        )
    ).first()
    if default_conversation is None:
        raise KeyError(f"default conversation not found for note: {note_id}")
    return _note_detail_from_row(
        note,
        default_conversation_id=default_conversation.id,
        active_conversation_id=_active_conversation_id(note, default_conversation.id),
    )


def save_note_snapshot(
    session: Session,
    owner_id: UUID,
    note_id: UUID,
    canvas_snapshot: str,
) -> MossUpdateNoteResponse:
    note = _require_note(session, owner_id, note_id)
    if note.canvas_snapshot == canvas_snapshot:
        return MossUpdateNoteResponse(
            note_id=note.id,
            title=note.title,
            display_title=note.display_title,
            effective_title=note.display_title or note.title,
            preview_text=note.preview_text,
            pinned_at=note.pinned_at,
            updated_at=note.updated_at,
        )

    metadata = extract_note_metadata(canvas_snapshot)
    note.title = metadata.title
    note.preview_text = metadata.preview_text
    note.canvas_snapshot = canvas_snapshot
    note.updated_at = utc_now()
    session.add(note)
    session.commit()
    session.refresh(note)
    return MossUpdateNoteResponse(
        note_id=note.id,
        title=note.title,
        display_title=note.display_title,
        effective_title=note.display_title or note.title,
        preview_text=note.preview_text,
        pinned_at=note.pinned_at,
        updated_at=note.updated_at,
    )


def update_note(
    session: Session,
    owner_id: UUID,
    note_id: UUID,
    *,
    display_title: object = _UNSET,
    pinned: object = _UNSET,
) -> MossUpdateNoteResponse:
    note = _require_note(session, owner_id, note_id)
    if display_title is not _UNSET:
        note.display_title = None if display_title is None else str(display_title).strip() or None
    if pinned is not _UNSET:
        note.pinned_at = utc_now() if bool(pinned) else None
    note.updated_at = utc_now()
    session.add(note)
    session.commit()
    session.refresh(note)
    return MossUpdateNoteResponse(
        note_id=note.id,
        title=note.title,
        display_title=note.display_title,
        effective_title=note.display_title or note.title,
        preview_text=note.preview_text,
        pinned_at=note.pinned_at,
        updated_at=note.updated_at,
    )


def delete_note(session: Session, owner_id: UUID, note_id: UUID) -> MossDeleteNoteResponse:
    note = _require_note(session, owner_id, note_id)
    note.deleted_at = utc_now()
    note.updated_at = utc_now()
    session.add(note)
    session.commit()
    session.refresh(note)
    assert note.deleted_at is not None
    return MossDeleteNoteResponse(note_id=note.id, deleted_at=note.deleted_at)


def list_note_conversations(
    session: Session,
    owner_id: UUID,
    note_id: UUID,
) -> MossConversationListResponse:
    note = _require_note(session, owner_id, note_id)
    default_conversation = session.exec(
        select(MossConversation).where(
            MossConversation.note_id == note.id,
            col(MossConversation.is_default).is_(True),
            col(MossConversation.deleted_at).is_(None),
        )
    ).first()
    if default_conversation is None:
        raise KeyError(f"default conversation not found for note: {note_id}")
    statement = (
        select(MossConversation)
        .where(
            MossConversation.owner_id == owner_id,
            MossConversation.note_id == note.id,
            col(MossConversation.deleted_at).is_(None),
        )
        .order_by(
            col(MossConversation.pinned_at).is_(None).asc(),
            col(MossConversation.pinned_at).desc(),
            col(MossConversation.is_default).desc(),
            col(MossConversation.updated_at).desc(),
        )
    )
    conversations = session.exec(statement).all()
    return MossConversationListResponse(
        conversations=[_conversation_summary_from_row(conversation) for conversation in conversations],
        active_conversation_id=_active_conversation_id(note, default_conversation.id),
    )


def create_conversation_for_note(
    session: Session,
    owner_id: UUID,
    note_id: UUID,
) -> MossCreateConversationResponse:
    note = _require_note(session, owner_id, note_id)
    now = utc_now()
    conversation = MossConversation(
        owner_id=owner_id,
        note_id=note_id,
        title=DEFAULT_NEW_CONVERSATION_TITLE,
        is_default=False,
        created_at=now,
        updated_at=now,
    )
    note.last_opened_conversation_id = conversation.id
    note.updated_at = now
    session.add(note)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return MossCreateConversationResponse(**_conversation_summary_from_row(conversation).model_dump())


def update_conversation(
    session: Session,
    owner_id: UUID,
    note_id: UUID,
    conversation_id: UUID,
    *,
    title: object = _UNSET,
    pinned: object = _UNSET,
) -> MossConversationSummary:
    conversation = _require_conversation(session, owner_id, note_id, conversation_id)
    if title is not _UNSET:
        cleaned = str(title).strip()
        if not cleaned:
            raise ValueError("conversation title cannot be empty")
        conversation.title = cleaned[:255]
    if pinned is not _UNSET:
        conversation.pinned_at = utc_now() if bool(pinned) else None
    conversation.updated_at = utc_now()
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return _conversation_summary_from_row(conversation)


def delete_conversation(
    session: Session,
    owner_id: UUID,
    note_id: UUID,
    conversation_id: UUID,
) -> MossDeleteConversationResponse:
    conversation = _require_conversation(session, owner_id, note_id, conversation_id)
    if conversation.is_default:
        raise ValueError("default conversation cannot be deleted")
    conversation.deleted_at = utc_now()
    conversation.pinned_at = None
    conversation.updated_at = utc_now()
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    assert conversation.deleted_at is not None

    note = _require_note(session, owner_id, note_id)
    if note.last_opened_conversation_id == conversation.id:
        default_conversation = session.exec(
            select(MossConversation).where(
                MossConversation.note_id == note.id,
                col(MossConversation.is_default).is_(True),
                col(MossConversation.deleted_at).is_(None),
            )
        ).first()
        if default_conversation is None:
            raise KeyError(f"default conversation not found for note: {note_id}")
        note.last_opened_conversation_id = default_conversation.id
        note.updated_at = utc_now()
        session.add(note)
        session.commit()

    return MossDeleteConversationResponse(
        conversation_id=conversation.id,
        deleted_at=conversation.deleted_at,
    )


def mark_conversation_opened(
    session: Session,
    owner_id: UUID,
    note_id: UUID,
    conversation_id: UUID,
) -> MossConversationSummary:
    conversation = _require_conversation(session, owner_id, note_id, conversation_id)
    note = _require_note(session, owner_id, note_id)
    now = utc_now()
    note.last_opened_conversation_id = conversation.id
    note.updated_at = now
    conversation.updated_at = now
    session.add(note)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return _conversation_summary_from_row(conversation)


def get_conversation_messages(
    session: Session,
    owner_id: UUID,
    note_id: UUID,
    conversation_id: UUID,
) -> MossConversationMessagesResponse:
    _require_conversation(session, owner_id, note_id, conversation_id)
    return _conversation_messages_empty()
