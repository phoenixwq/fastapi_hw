from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, Relationship, SQLModel
import uuid as uuid_pkg
from passlib.context import CryptContext
from .role import UserRoleLink

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def new_uuid() -> str:
    val = uuid_pkg.uuid4()
    while val.hex[0] == "0":
        val = uuid_pkg.uuid4()
    return str(val)


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
    uuid: str = Field(
        default_factory=new_uuid, nullable=False, sa_column_kwargs={'unique': True}
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

    def set_password(self, password: str) -> None:
        self.password = password_context.hash(password)

    def verify_password(self, password: str) -> bool:
        return password_context.verify(password, self.password)
