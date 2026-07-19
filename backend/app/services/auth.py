import hashlib
from uuid import UUID

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_user_id_from_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import LoginUser, RegisterUser, UpdateUser
from app.utils.exceptions import UserAlreadyExists
from fastapi import Response


class AuthService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def _create_access_token(self, user: User) -> str:
        return create_access_token(user)

    def _create_refresh_token(self, user: User) -> str:
        return create_refresh_token(user)

    def _decode_token(self, token: str) -> dict:
        return decode_token(token)

    async def create(self, credentials: RegisterUser) -> User:
        existing_user = await self.repository.get_by_email(credentials.email.lower())

        if existing_user:
            raise UserAlreadyExists()

        user = User(
            email=credentials.email.lower(),
            password_hash=hash_password(credentials.password),
            display_name=credentials.name,
        )

        return await self.repository.create(user)

    async def authenticate(
        self, credentials: LoginUser, response: Response
    ) -> tuple[User, str]:
        user = await self.repository.get_by_email(credentials.email.lower())

        if not user or not user.password_hash:
            raise ValueError("Invalid credentials")

        if not verify_password(credentials.password, user.password_hash):
            raise ValueError("Invalid credentials")

        access_token = self._create_access_token(user)

        refresh_token = self._create_refresh_token(user)

        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        await self.repository.save_refresh_token(user.id, token_hash)

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=60 * 60 * 24 * 30,
            path="/auth/v1/refresh",
        )

        return user, access_token

    async def refresh(self, refresh_token: str) -> tuple[User, str]:
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        stored_token = await self.repository.get_refresh_token(token_hash)

        if not stored_token or not stored_token.is_active:
            raise ValueError("Invalid refresh token")

        try:
            payload = self._decode_token(refresh_token)
        except Exception as exc:
            raise ValueError("Invalid refresh token") from exc

        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid refresh token")

        user = await self.repository.get_by_id(UUID(user_id))
        if not user:
            raise ValueError("User not found")

        await self.repository.deactivate_refresh_token(token_hash)

        new_refresh_token = self._create_refresh_token(user)
        new_token_hash = hashlib.sha256(new_refresh_token.encode()).hexdigest()
        await self.repository.save_refresh_token(user.id, new_token_hash)

        return user, self._create_access_token(user)

    async def get_current_user(self, token: str) -> User:
        try:
            user_id = get_user_id_from_token(token)
        except Exception as exc:
            raise ValueError("Invalid token") from exc

        user = await self.repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        return user

    async def update(self, user_id: UUID, data: UpdateUser) -> User:
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        if data.name is not None:
            user.display_name = data.name
        if data.avatar_url is not None:
            user.avatar_url = str(data.avatar_url)

        return await self.repository.update(user)

    async def logout(self, refresh_token: str | None) -> None:
        if not refresh_token:
            return

        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        await self.repository.deactivate_refresh_token(token_hash)

    async def delete(self, user_id: UUID) -> dict:
        return await self.repository.delete(user_id)
