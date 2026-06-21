from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response

from app.api.deps import CurrentUser
from app.core.config import settings
from app.moss.documents.service import (
    get_download_artifact,
    html_to_markdown,
    parse_uploaded_document,
    safe_filename,
    save_document,
)
from app.moss.schemas import (
    MossDocumentUploadResponse,
    MossExportDocumentRequest,
    MossSaveDocumentRequest,
    MossSaveDocumentResponse,
)

router = APIRouter(prefix="/moss/documents", tags=["moss-documents"])


@router.post("/upload", response_model=MossDocumentUploadResponse)
async def upload_moss_document(
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> Any:
    _ = current_user.id
    try:
        parsed = parse_uploaded_document(file.filename or "document.txt", await file.read())
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="Document must be UTF-8 encoded") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return MossDocumentUploadResponse(
        filename=parsed.filename,
        textContent=parsed.text,
        htmlContent=parsed.html,
    )


@router.post("/export")
def export_moss_document(
    payload: MossExportDocumentRequest,
    current_user: CurrentUser,
) -> Response:
    _ = current_user.id
    safe_name = safe_filename(payload.filename)
    if payload.format == "markdown":
        body = html_to_markdown(payload.content).encode("utf-8")
        return Response(
            content=body,
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}.md"'},
        )
    if payload.format == "html":
        return Response(
            content=payload.content.encode("utf-8"),
            media_type="text/html; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{safe_name}.html"'},
        )
    raise HTTPException(
        status_code=501,
        detail="PDF export is not enabled in the template-integrated backend yet",
    )


@router.post("/save", response_model=MossSaveDocumentResponse)
def save_moss_document(
    payload: MossSaveDocumentRequest,
    current_user: CurrentUser,
) -> MossSaveDocumentResponse:
    _ = current_user.id
    save_document(settings.MOSS_STORAGE_DIR, payload.doc_id, payload.content)
    return MossSaveDocumentResponse(docId=payload.doc_id)


@router.get("/download/{token}")
def download_moss_document(token: str, current_user: CurrentUser) -> Response:
    _ = current_user.id
    artifact = get_download_artifact(token)
    if artifact is None:
        raise HTTPException(status_code=404, detail="Download token not found")

    export_format = artifact.get("format", "markdown")
    content = artifact.get("content", "")
    extension = {"markdown": "md", "html": "html", "pdf": "pdf"}.get(export_format, "txt")
    media_type = {
        "markdown": "text/markdown; charset=utf-8",
        "html": "text/html; charset=utf-8",
        "pdf": "application/pdf",
    }.get(export_format, "text/plain; charset=utf-8")
    return Response(
        content=content.encode("utf-8"),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="moss-export.{extension}"'},
    )
