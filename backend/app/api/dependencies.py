from typing import Annotated

from app.database.session import get_session
from app.repositories.user import UserRepository
from app.services.auth import AuthService
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

SessionDep = Annotated[AsyncSession, Depends(get_session)]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/v1/login")


def get_user_service(session: SessionDep):
    repository = UserRepository(session)
    return AuthService(repository)


UserServiceDep = Annotated[AuthService, Depends(get_user_service)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]
