import json
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentUser, SessionDep
from app.moss.agent.runtime import stream_mock_agent_events
from app.moss.schemas import MossChatRequest
from app.moss.services import mark_conversation_opened, save_note_snapshot

router = APIRouter(prefix="/moss/agent", tags=["moss-agent"])


@router.post("/chat-stream")
def moss_chat_stream(
    session: SessionDep,
    current_user: CurrentUser,
    payload: MossChatRequest,
) -> StreamingResponse:
    try:
        if payload.note_id is not None and payload.conversation_id is not None:
            mark_conversation_opened(
                session,
                current_user.id,
                payload.note_id,
                payload.conversation_id,
            )
            save_note_snapshot(
                session,
                current_user.id,
                payload.note_id,
                payload.canvas_snapshot,
            )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    async def generator():
        async for event in stream_mock_agent_events(payload.user_input):
            yield _sse(event["event"], event.get("data", {}))
        yield _sse("done", {"status": "ok"})

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _sse(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
