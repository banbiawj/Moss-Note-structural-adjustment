from fastapi import APIRouter

from app.api.routes import (
    items,
    login,
    moss_agent,
    moss_conversations,
    moss_documents,
    moss_notes,
    private,
    users,
    utils,
)
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(moss_notes.router)
api_router.include_router(moss_conversations.router)
api_router.include_router(moss_documents.router)
api_router.include_router(moss_agent.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
