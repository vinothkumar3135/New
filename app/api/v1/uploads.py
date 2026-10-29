"""Uploads and file serving API router."""

from typing import Any, Dict
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response
from app.dependencies.auth import get_current_user
from app.dependencies.services import get_storage_service
from app.services.storage_service import StorageService

router = APIRouter(tags=["Uploads"])

@router.post("/uploads")
async def upload_file(
    file: UploadFile = File(...),
    user: Dict[str, Any] = Depends(get_current_user),
    storage_service: StorageService = Depends(get_storage_service),
):
    """Upload a photo (JPG, PNG, GIF, WEBP up to 8MB) via object storage."""
    return await storage_service.upload_file(file, user)

@router.get("/files/{path:path}")
async def download_file(
    path: str,
    storage_service: StorageService = Depends(get_storage_service),
):
    """Public file download / image serving endpoint."""
    data, content_type = await storage_service.download_file(path)
    return Response(
        content=data,
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )
