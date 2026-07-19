from typing import Annotated

from app.api.dependencies import TokenDep, UserServiceDep
from app.schemas.auth import (
    LoginUser,
    ReadUser,
    RegisterUser,
    TokenResponse,
    UpdateUser,
)
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import HttpUrl

router = APIRouter(prefix="/auth/v1", tags=["Authentication"])


def _serialize_user(user) -> ReadUser:
    return ReadUser(
        id=user.id,
        name=user.display_name or user.email,
        avatar_url=HttpUrl("https://avatars.githubusercontent.com/default?v=4"),
        email=user.email,
        is_active=user.is_active,
        is_verified=user.is_email_verified,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.post("/signup", response_model=ReadUser, status_code=status.HTTP_201_CREATED)
async def signup(user_data: RegisterUser, service: UserServiceDep):
    user = await service.create(user_data)
    return _serialize_user(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: UserServiceDep,
    response: Response,
):
    credentials = LoginUser(email=form_data.username, password=form_data.password)

    try:
        user, access_token = await service.authenticate(credentials, response)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        ) from exc

    return TokenResponse(access_token=access_token, user=_serialize_user(user))


@router.get("/me", response_model=ReadUser)
async def current_user(token: TokenDep, service: UserServiceDep):
    try:
        user = await service.get_current_user(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc

    return _serialize_user(user)


@router.put("/me", response_model=ReadUser)
async def update(user_data: UpdateUser, token: TokenDep, service: UserServiceDep):
    try:
        user = await service.get_current_user(token)
        updated_user = await service.update(user.id, user_data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc

    return _serialize_user(updated_user)


@router.delete("/me")
async def delete(token: TokenDep, service: UserServiceDep):
    try:
        user = await service.get_current_user(token)
        await service.delete(user.id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc

    return {"message": "User deleted successfully"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    service: UserServiceDep,
):
    refresh_token_value = request.cookies.get("refresh_token")
    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing"
        )

    try:
        user, access_token = await service.refresh(refresh_token_value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        ) from exc

    return TokenResponse(access_token=access_token, user=_serialize_user(user))


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    service: UserServiceDep,
):
    refresh_token_value = request.cookies.get("refresh_token")
    await service.logout(refresh_token_value)

    response.delete_cookie(
        key="refresh_token",
        path="/auth/v1/refresh",
    )

    return {"message": "Logged out successfully"}
