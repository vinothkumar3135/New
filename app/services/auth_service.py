"""Authentication service implementing registration, login, and user sessions."""

from typing import Any, Dict
from app.core.exceptions import BadRequestException, UnauthorizedException
from app.core.security import hash_password, verify_password, create_access_token
from app.repositories.user_repository import UserRepository
from app.schemas.auth import RegisterIn, LoginIn, TokenResponse
from app.schemas.user import UserResponse, UserUpdate
from app.utils.datetime import new_id, now_iso
from app.utils.response import normalize_user

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register(self, data: RegisterIn) -> TokenResponse:
        email = data.email.lower().strip()
        existing = await self.user_repo.get_by_email(email)
        if existing:
            raise BadRequestException("Email already registered")

        user_doc = {
            "id": new_id(),
            "name": data.name.strip(),
            "email": email,
            "password": hash_password(data.password),
            "role": data.role,
            "phone": data.phone,
            "avatar": None,
            "created_at": now_iso(),
        }
        await self.user_repo.create_user(user_doc)
        token = create_access_token(user_doc["id"])
        clean_user = normalize_user(user_doc)
        return TokenResponse(token=token, user=UserResponse(**clean_user))

    async def login(self, data: LoginIn) -> TokenResponse:
        email = data.email.lower().strip()
        user_doc = await self.user_repo.get_by_email(email)
        if not user_doc or not verify_password(data.password, user_doc.get("password", "")):
            raise UnauthorizedException("Invalid credentials")

        token = create_access_token(user_doc["id"])
        clean_user = normalize_user(user_doc)
        return TokenResponse(token=token, user=UserResponse(**clean_user))

    async def get_me(self, current_user: Dict[str, Any]) -> UserResponse:
        clean_user = normalize_user(current_user)
        return UserResponse(**clean_user)

    async def update_me(self, current_user: Dict[str, Any], data: UserUpdate) -> UserResponse:
        updates = {k: v for k, v in data.model_dump().items() if v is not None}
        fresh = await self.user_repo.update_profile(current_user["id"], updates)
        clean_user = normalize_user(fresh or current_user)
        return UserResponse(**clean_user)
