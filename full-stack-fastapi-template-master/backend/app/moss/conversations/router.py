from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.moss.schemas import (
    MossConversationListResponse,
    MossConversationMessagesResponse,
    MossConversationSummary,
    MossCreateConversationResponse,
    MossDeleteConversationResponse,
    MossUpdateConversationRequest,
)
from app.moss.services import (
    _UNSET,
    create_conversation_for_note,
    delete_conversation,
    get_conversation_messages,
    list_note_conversations,
    update_conversation,
)

router = APIRouter(prefix="/moss/notes/{note_id}/conversations", tags=["moss-conversations"])


@router.get("/", response_model=MossConversationListResponse)
def read_moss_note_conversations(
    session: SessionDep,
    current_user: CurrentUser,
    note_id: UUID,
) -> Any:
    try:
        return list_note_conversations(session, current_user.id, note_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/", response_model=MossCreateConversationResponse)
def create_moss_note_conversation(
    session: SessionDep,
    current_user: CurrentUser,
    note_id: UUID,
) -> Any:
    try:
        return create_conversation_for_note(session, current_user.id, note_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{conversation_id}", response_model=MossConversationSummary)
def update_moss_note_conversation(
    session: SessionDep,
    current_user: CurrentUser,
    note_id: UUID,
    conversation_id: UUID,
    payload: MossUpdateConversationRequest,
) -> Any:
    try:
        title = payload.title if "title" in payload.model_fields_set else _UNSET
        pinned = payload.pinned if "pinned" in payload.model_fields_set else _UNSET
        return update_conversation(
            session,
            current_user.id,
            note_id,
            conversation_id,
            title=title,
            pinned=pinned,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/{conversation_id}", response_model=MossDeleteConversationResponse)
def delete_moss_note_conversation(
    session: SessionDep,
    current_user: CurrentUser,
    note_id: UUID,
    conversation_id: UUID,
) -> Any:
    try:
        return delete_conversation(session, current_user.id, note_id, conversation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{conversation_id}/messages", response_model=MossConversationMessagesResponse)
def read_moss_note_conversation_messages(
    session: SessionDep,
    current_user: CurrentUser,
    note_id: UUID,
    conversation_id: UUID,
) -> Any:
    try:
        return get_conversation_messages(
            session,
            current_user.id,
            note_id,
            conversation_id,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
