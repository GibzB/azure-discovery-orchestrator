"""
API Router — aggregates all route groups
"""
from fastapi import APIRouter

from app.api.routes import chat, sessions, reports, voice

api_router = APIRouter()
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(voice.router, prefix="/voice", tags=["voice"])
