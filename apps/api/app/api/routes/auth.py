from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.core.config import get_settings
from app.core.rate_limit import get_login_rate_limiter
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.services.auth import AuthService

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    settings = get_settings()
    limiter = get_login_rate_limiter()
    client_host = request.client.host if request.client is not None else "unknown"
    rate_limit_key = f"{client_host}:{payload.email.strip().lower()}"
    rate_limit_state = await limiter.evaluate(
        key=rate_limit_key,
        limit=settings.login_rate_limit_attempts,
        window_seconds=settings.login_rate_limit_window_seconds,
    )
    if not rate_limit_state.allowed:
        response.headers["Retry-After"] = str(rate_limit_state.retry_after_seconds)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
            headers={"Retry-After": str(rate_limit_state.retry_after_seconds)},
        )

    try:
        token, user = await AuthService(session).login(
            email=payload.email,
            password=payload.password,
        )
    except HTTPException:
        await limiter.record_failure(
            key=rate_limit_key,
            window_seconds=settings.login_rate_limit_window_seconds,
        )
        raise

    await limiter.reset(key=rate_limit_key)
    return TokenResponse(access_token=token, user=UserResponse.from_model(user))


@router.get("/me", response_model=UserResponse)
async def me(current_user=Depends(get_current_user)) -> UserResponse:
    return UserResponse.from_model(current_user)
