from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: str = Field(..., pattern=r"^\S+@\S+\.\S+$")
    role: str = Field(default="analyst")
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    email: str | None = None
    role: str | None = None
    is_active: bool | None = None


class UserRead(UserBase):
    id: int
    organization_id: int | None = None
    mfa_enabled: bool = False
    last_login: datetime | None = None
    last_login_ip: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
