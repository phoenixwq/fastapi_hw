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


class JWTAuth:
    def __init__(self, access_cash, refresh_cash):
        self.blocked_access_tokens = access_cash
        self.active_refresh_tokens = refresh_cash

    def create_jwt_token(self, sub: str) -> Token:
        access_token = self.create_access_token(sub)
        refresh_token = self.create_refresh_token(sub)
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    def refresh_token(self, token: str) -> Token:
        decode_token = self.decode_token(token)
        sub = decode_token.get('sub')
        jwt_token = self.create_jwt_token(sub)
        payload = jwt.decode(jwt_token.refresh_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        jti = payload["jti"]
        self.active_refresh_tokens.add(sub, jti)
        return jwt_token

    def _create_token(self, sub: str, token_type: str, exp: int):
        now = datetime.now().timestamp()
        token_data = {
            "iat": now,
            "exp": now + exp + 1000,
            "type": token_type,
            "jti": str(uuid.uuid4()),
            "sub": sub
        }

        token = jwt.encode(
            token_data,
            JWT_SECRET_KEY,
            algorithm=JWT_ALGORITHM
        )
        return token

    def create_access_token(self, sub: str) -> str:
        return self._create_token(sub, "access", JWT_ACCESS_EXPIRE_SECONDS)

    def create_refresh_token(self, sub: str) -> str:
        return self._create_token(sub, "refresh", JWT_REFRESH_EXPIRE_SECONDS)

    def decode_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail='Expired signature')
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail='Invalid token')

    def token_is_blocked(self, jti: str) -> bool:
        if self.blocked_access_tokens.get(jti):
            return True
        return False

    def block_access_token(self, jti: str) -> None:
        self.blocked_access_tokens.set(jti, "blocked")

    def add_refresh_token(self, token: str):
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        sub, jti = payload["jti"], payload["sub"]
        self.active_refresh_tokens.add(sub, jti)

    def remove_refresh_token(self, sub: str, jti: str) -> None:
        current_tokens = self.active_refresh_tokens.get(sub)
        try:
            current_tokens.pop(current_tokens.index(jti))
        except ValueError:
            # TODO
            ...
        self.active_refresh_tokens.clean(sub)
        if current_tokens:
            self.active_refresh_tokens.add(sub, *current_tokens)

    def remove_all_refresh_tokens(self, sub: str) -> None:
        self.active_refresh_tokens.clean(sub)

    def check_refresh_token(self, sub: str, jti: str) -> bool:
        current_tokens = self.active_refresh_tokens.get(sub)
        return True if jti in current_tokens else False
