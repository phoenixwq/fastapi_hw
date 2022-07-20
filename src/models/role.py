from typing import Optional, List
from sqlmodel import Field, Relationship, SQLModel

__all__ = ("Role", "UserRoleLink",)


class UserRoleLink(SQLModel, table=True):
    role_id: Optional[int] = Field(
        default=None, foreign_key="role.id", primary_key=True
    )
    user_id: Optional[int] = Field(
        default=None, foreign_key="user.id", primary_key=True
    )


class Role(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(sa_column_kwargs={'unique': True})
    users: List["User"] = Relationship(back_populates="roles", link_model=UserRoleLink)
