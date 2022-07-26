from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, UUID4

__all__ = ("UserBase", "UserLogin", "UserCreate", "UserUpdate", "UserAbout")


class UserBase(BaseModel):
    username: str


class UserLogin(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class UserCreate(UserBase):
    password: str
    email: EmailStr


class UserAbout(UserBase):
    username: str
    email: EmailStr
    uuid: UUID4
    created_at: datetime
    is_superuser: bool
    is_active: bool
