from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.moss.schemas import (
    MossDeleteNoteResponse,
    MossNoteDetail,
    MossNoteListResponse,
    MossSaveSnapshotRequest,
    MossUpdateNoteRequest,
    MossUpdateNoteResponse,
)
from app.moss.services import (
    _UNSET,
    create_note,
    delete_note,
    get_note,
    list_notes,
    save_note_snapshot,
    update_note,
)

router = APIRouter(prefix="/moss/notes", tags=["moss-notes"])


@router.get("/", response_model=MossNoteListResponse)
def read_moss_notes(session: SessionDep, current_user: CurrentUser) -> Any:
    return list_notes(session, current_user.id)


@router.post("/", response_model=MossNoteDetail)
def create_moss_note(session: SessionDep, current_user: CurrentUser) -> Any:
    return create_note(session, current_user.id)


@router.get("/{note_id}", response_model=MossNoteDetail)
def read_moss_note(
    session: SessionDep,
    current_user: CurrentUser,
    note_id: UUID,
) -> Any:
    try:
        return get_note(session, current_user.id, note_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{note_id}/snapshot", response_model=MossUpdateNoteResponse)
def save_moss_note_snapshot(
    session: SessionDep,
    current_user: CurrentUser,
    note_id: UUID,
    payload: MossSaveSnapshotRequest,
) -> Any:
    try:
        return save_note_snapshot(
            session,
            current_user.id,
            note_id,
            payload.canvas_snapshot,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{note_id}", response_model=MossUpdateNoteResponse)
def update_moss_note(
    session: SessionDep,
    current_user: CurrentUser,
    note_id: UUID,
    payload: MossUpdateNoteRequest,
) -> Any:
    try:
        display_title = (
            payload.display_title
            if "display_title" in payload.model_fields_set
            else _UNSET
        )
        pinned = payload.pinned if "pinned" in payload.model_fields_set else _UNSET
        return update_note(
            session,
            current_user.id,
            note_id,
            display_title=display_title,
            pinned=pinned,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/{note_id}", response_model=MossDeleteNoteResponse)
def delete_moss_note(
    session: SessionDep,
    current_user: CurrentUser,
    note_id: UUID,
) -> Any:
    try:
        return delete_note(session, current_user.id, note_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
