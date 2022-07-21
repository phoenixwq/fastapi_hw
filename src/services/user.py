import uuid
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Union
import jwt
from fastapi import Depends
from sqlmodel import Session
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi import status
from src.api.v1.schemas.auth import Token
from src.api.v1.schemas.users import UserCreate, UserLogin
from src.core.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_EXPIRE_SECONDS, JWT_REFRESH_EXPIRE_SECONDS
from src.db import AbstractCache, get_cache, get_session
from src.models import User
from src.services import ServiceMixin
from src.db import (AbstractCache,
                    CacheToken,
                    get_cache,
                    get_session,
                    get_access_cash,
                    get_refresh_cash)

__all__ = ("UserService", "get_user_service")

from src.services.auth import JWTAuth


class UserService(ServiceMixin):
    def __init__(self,
                 cache: AbstractCache,
                 access_cash: AbstractCache,
                 refresh_cash: CacheToken,
                 session: Session):
        super().__init__(cache=cache, session=session)
        self.auth = JWTAuth(access_cash, refresh_cash)

    def create_user(self, user: UserCreate) -> dict:
        """Создать пользователя."""
        if self.get_user_by_username(user.username) is not None:
            raise ValueError("User with this username already exists.")

        if self.get_user_by_email(user.email) is not None:
            raise ValueError("User with this email already exists.")

        new_user = User(username=user.username, email=user.email)
        new_user.set_password(user.password)
        self.session.add(new_user)
        self.session.commit()
        self.session.refresh(new_user)
        user_data = new_user.dict()
        # user_data["roles"] = []
        return {"msg": "User created.", "user": user_data}

    def get_user_by_username(self, username: str) -> Union[User, None]:
        """Получить пользователя по username"""
        user = self.session.query(User).filter(User.username == username).first()
        return user

    def get_user_by_uuid(self, uuid: str) -> Union[User, None]:
        """Получить пользователя по uuid"""
        user = self.session.query(User).filter(User.uuid == uuid).first()
        return user

    def get_user_by_email(self, email: str) -> Union[User, None]:
        """Получить пользователя по uuid"""
        user = self.session.query(User).filter(User.uuid == email).first()
        return user

    def login_user(self, login_data: UserLogin):
        user = self.get_user_by_username(login_data.username)
        if not user:
            # TODO errors
            raise ValueError(str(login_data))
        if not user.verify_password(login_data.password):
            raise ValueError(str(login_data))
        jwt_token = self.auth.create_jwt_token(user.uuid)
        self.auth.add_refresh_token(jwt_token.refresh_token)
        return jwt_token

    def current_user(self, token: str):
        payload = self.auth.decode_token(token)
        if payload is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        jti = payload.get("jti")
        if self.auth.token_is_blocked(jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token was blocked"
            )
        sub: str = payload.get("sub")
        return self.get_user_by_uuid(sub)

    def update_user(self, user: User, data: dict) -> (User, str):
        for key, value in data.items():
            setattr(user, key, value)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        access_token = self.auth.create_access_token(user.uuid)
        return user, access_token

    def refresh_token(self, token: str) -> Token:
        return self.auth.refresh_token(token)

    def logout(self, token: str):
        payload = self.auth.decode_token(token)
        jti, sub = payload["jti"], payload["sub"]
        self.auth.block_access_token(jti)
        self.auth.remove_refresh_token(sub, jti)

    def logout_all(self, token: str):
        payload = self.auth.decode_token(token)
        jti, sub = payload["jti"], payload["sub"]
        self.auth.block_access_token(jti)
        self.auth.remove_all_refresh_tokens(sub)


# get_post_service — это провайдер PostService. Синглтон
@lru_cache()
def get_user_service(
        cache: AbstractCache = Depends(get_cache),
        access_cash: AbstractCache = Depends(get_access_cash),
        refresh_cash: CacheToken = Depends(get_refresh_cash),
        session: Session = Depends(get_session),
) -> UserService:
    return UserService(cache=cache,
                       access_cash=access_cash,
                       refresh_cash=refresh_cash,
                       session=session)
