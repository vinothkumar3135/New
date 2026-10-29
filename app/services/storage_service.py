"""Object storage service integrating Emergent object store and file metadata."""

import logging
import uuid
import requests
from typing import Any, Dict, Tuple
from fastapi import UploadFile
from app.core.config import settings
from app.core.constants import ALLOWED_MIME_TYPES, MAX_UPLOAD_BYTES
from app.core.exceptions import AppException, BadRequestException, NotFoundException
from app.repositories.file_repository import FileRepository
from app.utils.datetime import new_id, now_iso

logger = logging.getLogger("infoez.storage")

class StorageService:
    def __init__(self, file_repo: FileRepository):
        self.file_repo = file_repo
        self._storage_key: str = ""

    def init_storage(self, force: bool = False) -> str:
        if self._storage_key and not force:
            return self._storage_key
        if not settings.EMERGENT_LLM_KEY:
            raise RuntimeError("EMERGENT_LLM_KEY missing in environment")
        resp = requests.post(
            f"{settings.storage_url}/init",
            json={"emergent_key": settings.EMERGENT_LLM_KEY},
            timeout=30,
        )
        resp.raise_for_status()
        self._storage_key = resp.json()["storage_key"]
        return self._storage_key

    def put_object(self, path: str, data: bytes, content_type: str) -> Dict[str, Any]:
        key = self.init_storage()
        try:
            resp = requests.put(
                f"{settings.storage_url}/objects/{path}",
                headers={"X-Storage-Key": key, "Content-Type": content_type},
                data=data,
                timeout=120,
            )
            resp.raise_for_status()
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code in (403, 404):
                key = self.init_storage(force=True)
                resp = requests.put(
                    f"{settings.storage_url}/objects/{path}",
                    headers={"X-Storage-Key": key, "Content-Type": content_type},
                    data=data,
                    timeout=120,
                )
                resp.raise_for_status()
            else:
                raise
        return resp.json()

    def get_object(self, path: str) -> Tuple[bytes, str]:
        key = self.init_storage()
        resp = requests.get(
            f"{settings.storage_url}/objects/{path}",
            headers={"X-Storage-Key": key},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.content, resp.headers.get("Content-Type", "application/octet-stream")

    async def upload_file(self, file: UploadFile, current_user: Dict[str, Any]) -> Dict[str, Any]:
        filename = file.filename or ""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
        if ext not in ALLOWED_MIME_TYPES:
            raise BadRequestException("Only jpg, jpeg, png, gif, webp allowed")

        data = await file.read()
        if len(data) > MAX_UPLOAD_BYTES:
            raise AppException(status_code=413, detail="File too large (max 8MB)")

        content_type = ALLOWED_MIME_TYPES[ext]
        storage_path = f"infoez/uploads/{current_user['id']}/{uuid.uuid4()}.{ext}"

        try:
            result = self.put_object(storage_path, data, content_type)
        except Exception as e:
            logger.exception(f"Upload failed: {e}")
            raise AppException(status_code=500, detail=f"Storage error: {e}")

        await self.file_repo.create_file_record({
            "id": new_id(),
            "user_id": current_user["id"],
            "storage_path": result["path"],
            "original_filename": file.filename,
            "content_type": content_type,
            "size": result.get("size", len(data)),
            "is_deleted": False,
            "created_at": now_iso(),
        })

        public_url = f"/api/files/{result['path']}"
        return {
            "path": result["path"],
            "url": public_url,
            "size": result.get("size", len(data)),
        }

    async def download_file(self, path: str) -> Tuple[bytes, str]:
        rec = await self.file_repo.get_by_path(path)
        if not rec:
            raise NotFoundException("File not found")
        try:
            data, ctype = self.get_object(path)
        except Exception:
            raise NotFoundException("File not found")
        return data, rec.get("content_type", ctype)
