from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.domain.enums import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID
    organization_id: UUID
    email: EmailStr
    full_name: str
    role: UserRole

    @classmethod
    def from_model(cls, user: object) -> UserResponse:
        return cls.model_validate(user, from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
