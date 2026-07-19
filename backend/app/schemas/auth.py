from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, HttpUrl


class ReadUser(BaseModel):
    id: UUID
    name: str
    avatar_url: HttpUrl
    email: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class RegisterUser(BaseModel):
    name: str
    email: str
    password: str


class LoginUser(BaseModel):
    email: str
    password: str


class UpdateUser(BaseModel):
    name: str | None = None
    avatar_url: HttpUrl | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: ReadUser
