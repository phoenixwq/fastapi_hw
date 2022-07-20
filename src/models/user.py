from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, Relationship, SQLModel
import uuid as uuid_pkg
from .role import UserRoleLink


__all__ = ("User",)


class User(SQLModel, table=True):
    id: Optional[int] = Field(
        default=None, primary_key=True,
    )
    username: str = Field(
        sa_column_kwargs={'unique': True}, nullable=False
    )
    email: str = Field(
        sa_column_kwargs={'unique': True}, nullable=False
    )
    uuid: uuid_pkg.UUID = Field(
        default_factory=uuid_pkg.uuid4, nullable=False, sa_column_kwargs={'unique': True}
    )
    created_at: datetime = Field(
        default=datetime.utcnow(), nullable=False
    )
    roles: List["Role"] = Relationship(
        back_populates="users", link_model=UserRoleLink
    )
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    is_totp_enabled: bool = Field(default=False)
    password: str = Field(nullable=False)
