from functools import lru_cache
from typing import Union
from sqlmodel import Session
from fastapi import HTTPException, Depends, status
from redis import Redis

import src.auth as auth
from src.api.v1.schemas.users import UserCreate, UserLogin
from src.models import User
from src.services import ServiceMixin
from src.db import (
    AbstractCache,
    get_cache,
    get_session,
    get_access_cash,
    get_refresh_cash
)

__all__ = ("UserService", "get_user_service")


class UserService(ServiceMixin):
    def __init__(self,
                 cache: AbstractCache,
                 access_cash: Redis,
                 refresh_cash: Redis,
                 session: Session):
        super().__init__(cache=cache, session=session)
        self.active_refresh_tokens = refresh_cash
        self.blocked_access_tokens = access_cash

    def create_user(self, user: UserCreate) -> User:
        """Создать пользователя."""
        if self.get_user_by_username(user.username) is not None:
            raise HTTPException(
                status_code=400, detail="User with this username already exists."
            )

        new_user = User(username=user.username, email=user.email)
        new_user.set_password(user.password)
        self.session.add(new_user)
        self.session.commit()
        self.session.refresh(new_user)
        return new_user

    def get_user_by_username(self, username: str) -> Union[User, None]:
        """Получить пользователя по username"""
        user = self.session.query(User).filter(User.username == username).first()
        return user

    def get_user_by_uuid(self, uuid: str) -> Union[User, None]:
        """Получить пользователя по uuid"""
        user = self.session.query(User).filter(User.uuid == uuid).first()
        return user

    def login_user(self, login_data: UserLogin):
        """Вход пользователя по username и password"""
        user = self.get_user_by_username(login_data.username)
        if not user:
            raise HTTPException(
                status_code=401, detail="User with this login does not exist"
            )
        if not user.verify_password(login_data.password):
            raise HTTPException(
                status_code=401, detail="Incorrect login or password"
            )
        return {
            "access_token": self.create_access_token(user.uuid),
            "refresh_token": self.create_refresh_token(user.uuid)
        }

    def current_user(self, token: str):
        """Получить текущего пользователя"""
        payload = auth.decode_token(token)
        if payload is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        jti = payload.get("jti")
        if self.token_is_blocked(jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token was blocked"
            )
        user_uuid: str = payload.get("user_uuid")
        return self.get_user_by_uuid(user_uuid)

    def update_user(self, user: User, data: dict) -> User:
        "Обновление информации пользователя"
        for key, value in data.items():
            setattr(user, key, value)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def logout(self, token: str):
        """Выход с одного устройства"""
        payload = auth.decode_token(token)
        jti, user_uuid = payload["jti"], payload["user_uuid"]
        self.block_access_token(jti)

    def logout_all(self, token: str):
        """"Выход со всех устройств"""
        payload = auth.decode_token(token)
        jti, user_uuid = payload["jti"], payload["user_uuid"]
        self.block_access_token(jti)
        self.active_refresh_tokens.delete(user_uuid)

    def create_refresh_token(self, user_uuid: str) -> str:
        subject = {"user_uuid": user_uuid}
        refresh_token = auth.create_refresh_token(subject)
        jti: str = auth.get_jti(refresh_token)
        self.active_refresh_tokens.lpush(user_uuid, jti)
        return refresh_token

    def create_access_token(self, user_uuid: str):
        subject = {"user_uuid": user_uuid}
        return auth.create_access_token(subject)

    def block_access_token(self, jti: str) -> None:
        self.blocked_access_tokens.set(jti, 1)

    def token_is_blocked(self, jti: str) -> bool:
        if self.blocked_access_tokens.get(jti):
            return True
        return False


# get_post_service — это провайдер PostService. Синглтон
@lru_cache()
def get_user_service(
        cache: AbstractCache = Depends(get_cache),
        access_cash: Redis = Depends(get_access_cash),
        refresh_cash: Redis = Depends(get_refresh_cash),
        session: Session = Depends(get_session),

) -> UserService:
    return UserService(
        cache=cache,
        access_cash=access_cash,
        refresh_cash=refresh_cash,
        session=session
    )
