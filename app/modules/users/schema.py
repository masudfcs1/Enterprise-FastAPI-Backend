"""
User Pydantic schemas — request and response contracts for user management.
Sensitive attributes like hashed passwords are never exposed.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.shared.constants import UserRole


# ── Request Schemas ───────────────────────────────────────
class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=128)
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)


class UserUpdate(BaseModel):
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    username: str | None = Field(default=None, min_length=3, max_length=100)


class UserUpdateRole(BaseModel):
    role: UserRole


# ── Response Schemas ──────────────────────────────────────
class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    first_name: str | None = None
    last_name: str | None = None
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    id: str
    email: str
    username: str
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
