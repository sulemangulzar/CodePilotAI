from uuid import UUID

from app.models.token import RefreshToken
from app.models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_email(self, email: str) -> User | None:
        user = await self.session.execute(select(User).where(User.email == email))
        result = user.scalar_one_or_none()

        return result

    async def get_by_id(self, id: UUID) -> User | None:
        user = await self.session.execute(select(User).where(User.id == id))
        result = user.scalar_one_or_none()

        return result

    async def update(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def save_refresh_token(self, user_id: UUID, token_hash: str) -> RefreshToken:
        token = RefreshToken(user_id=user_id, token_hash=token_hash)
        self.session.add(token)
        await self.session.commit()
        await self.session.refresh(token)
        return token

    async def get_refresh_token(self, token_hash: str) -> RefreshToken | None:
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def deactivate_refresh_token(self, token_hash: str) -> None:
        token = await self.get_refresh_token(token_hash)
        if token is not None:
            token.is_active = False
            await self.session.commit()

    async def delete(self, id: UUID):
        user = await self.get_by_id(id)
        if user is None:
            raise ValueError("User not found")
        await self.session.delete(user)
        await self.session.commit()
        return {"message": "deleted"}
