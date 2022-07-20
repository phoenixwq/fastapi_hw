from datetime import datetime

from pydantic import BaseModel, EmailStr, UUID4


__all__ = ("UserBase", "UserLogin", "UserCreate", "UserUpdate", "UserAbout")


class UserBase(BaseModel):
    username: str


class UserLogin(UserBase):
    password: str


class UserUpdate(UserBase):
    email: EmailStr


class UserCreate(UserBase):
    password: str
    email: EmailStr


class UserAbout(UserBase):
    email: EmailStr
    password: str
    uuid: UUID4
    created_at: datetime
    is_superuser: bool
