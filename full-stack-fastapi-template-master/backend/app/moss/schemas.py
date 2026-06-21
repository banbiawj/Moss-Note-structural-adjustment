from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlmodel import SQLModel


class MossNoteCreateResponse(SQLModel):
    note_id: UUID
    default_conversation_id: UUID
    active_conversation_id: UUID
    title: str
    display_title: str | None = None
    effective_title: str
    preview_text: str
    canvas_snapshot: str
    pinned_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class MossNoteSummary(SQLModel):
    note_id: UUID
    default_conversation_id: UUID
    active_conversation_id: UUID
    title: str
    display_title: str | None = None
    effective_title: str
    preview_text: str
    pinned_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class MossNoteListResponse(SQLModel):
    notes: list[MossNoteSummary]


class MossNoteDetail(MossNoteCreateResponse):
    last_opened_conversation_id: UUID | None = None


class MossSaveSnapshotRequest(SQLModel):
    canvas_snapshot: str = ""


class MossUpdateNoteRequest(SQLModel):
    display_title: str | None = None
    pinned: bool | None = None


class MossUpdateNoteResponse(SQLModel):
    note_id: UUID
    title: str
    display_title: str | None = None
    effective_title: str
    preview_text: str
    pinned_at: datetime | None = None
    updated_at: datetime


class MossDeleteNoteResponse(SQLModel):
    note_id: UUID
    deleted_at: datetime


class MossConversationSummary(SQLModel):
    conversation_id: UUID
    note_id: UUID
    title: str
    is_default: bool
    pinned_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class MossConversationListResponse(SQLModel):
    conversations: list[MossConversationSummary]
    active_conversation_id: UUID


class MossCreateConversationResponse(MossConversationSummary):
    pass


class MossUpdateConversationRequest(SQLModel):
    title: str | None = None
    pinned: bool | None = None


class MossDeleteConversationResponse(SQLModel):
    conversation_id: UUID
    deleted_at: datetime


class MossConversationMessage(SQLModel):
    role: Literal["user", "ai"]
    content: str


class MossConversationMessagesResponse(SQLModel):
    messages: list[MossConversationMessage]


class MossDocumentUploadResponse(BaseModel):
    status: str = "success"
    filename: str
    text_content: str = Field(alias="textContent")
    html_content: str = Field(alias="htmlContent")

    model_config = ConfigDict(populate_by_name=True)


class MossExportDocumentRequest(BaseModel):
    format: Literal["markdown", "html", "pdf"]
    content: str
    filename: str = "moss-document"


class MossSaveDocumentRequest(BaseModel):
    doc_id: str = Field(default="doc-current", alias="docId")
    content: str

    model_config = ConfigDict(populate_by_name=True)


class MossSaveDocumentResponse(BaseModel):
    status: str = "success"
    message: str = "Saved successfully"
    doc_id: str = Field(alias="docId")

    model_config = ConfigDict(populate_by_name=True)


class MossChatContext(BaseModel):
    document_html: str | None = Field(default=None, alias="documentHTML")
    cursor_position: str | None = Field(default=None, alias="cursorPosition")
    history: list[dict] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class MossChatRequest(BaseModel):
    session_id: str = Field(default_factory=lambda: f"session-{uuid4().hex}")
    note_id: UUID | None = None
    conversation_id: UUID | None = None
    user_input: str = ""
    focus_element_id: str | None = None
    focus_block_id: str | None = None
    canvas_snapshot: str = ""

    message: str | None = None
    context: MossChatContext | None = None

    @model_validator(mode="after")
    def normalize_legacy_payload(self) -> "MossChatRequest":
        if not self.user_input and self.message:
            self.user_input = self.message
        if self.context:
            if not self.canvas_snapshot and self.context.document_html:
                self.canvas_snapshot = self.context.document_html
            if not self.focus_element_id and self.context.cursor_position:
                self.focus_element_id = self.context.cursor_position
        if not self.user_input.strip():
            raise ValueError("user_input/message cannot be empty")
        return self


class MossChatChunk(SQLModel):
    content: str
    done: bool = True


class MossHealthResponse(SQLModel):
    status: str = "ok"
    service: str = "moss-backend"
