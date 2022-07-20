import uuid
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Union
import jwt
from fastapi import Depends
from sqlmodel import Session

from src.api.v1.schemas.auth import Token
from src.api.v1.schemas.users import UserCreate, UserLogin
from src.core.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_EXPIRE_SECONDS, JWT_REFRESH_EXPIRE_SECONDS
from src.db import AbstractCache, get_cache, get_session
from src.models import User
from src.services import ServiceMixin

__all__ = ("UserService", "get_user_service")


class UserService(ServiceMixin):
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
        user_data["roles"] = []
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
            raise ValueError("")
        if not user.verify_password(login_data.password):
            raise ValueError
        return self.create_jwt_token(user)

    def create_jwt_token(self, user) -> Token:
        sub: str = user.uuid
        access_token = self.create_access_token(sub)
        refresh_token = self.create_refresh_token(sub)
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    def refresh_token(self, refresh_token: str) -> Token:
        decode_token = jwt.decode(
            refresh_token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )
        uuid = decode_token.get('sub')
        user = self.get_user_by_uuid(uuid)
        return self.create_jwt_token(user=user)

    def _create_token(self, sub: str, token_type: str, exp: int, claims: dict = None):
        now = datetime.now(tz=timezone.utc) + timedelta(minutes=exp)
        token_data = {
            "iat": now,
            "nbf": now,
            "exp": datetime.utcnow() + timedelta(minutes=exp),
            "type": token_type,
            "jti": str(uuid.uuid4()),
            "sub": sub,
        }

        if claims is not None:
            token_data.update(claims)

        token = jwt.encode(
            token_data,
            JWT_SECRET_KEY,
            algorithm=JWT_ALGORITHM
        )
        return token

    def create_access_token(self, sub, claims=None):
        return self._create_token(sub, "access", JWT_ACCESS_EXPIRE_SECONDS, claims)

    def create_refresh_token(self, sub, claims=None):
        return self._create_token(sub, "refresh", JWT_REFRESH_EXPIRE_SECONDS, claims)


# get_post_service — это провайдер PostService. Синглтон
@lru_cache()
def get_user_service(
        cache: AbstractCache = Depends(get_cache),
        session: Session = Depends(get_session),
) -> UserService:
    return UserService(cache=cache, session=session)
