import jwt
import uuid
from datetime import datetime
from fastapi import HTTPException

from .schema import Token
from src.core.config import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    JWT_ACCESS_EXPIRE_SECONDS,
    JWT_REFRESH_EXPIRE_SECONDS
)




def create_tokens(subject: dict) -> Token:
    access_token = create_access_token(subject)
    refresh_token = create_refresh_token(subject)
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
    )


def create_access_token(subject: dict) -> str:
    return _create_token(subject, "access", JWT_ACCESS_EXPIRE_SECONDS)


def create_refresh_token(subject: dict) -> str:
    return _create_token(subject, "refresh", JWT_REFRESH_EXPIRE_SECONDS)


def _create_token(subject: dict, token_type: str, exp: int) -> str:
    if not isinstance(subject, dict):
        raise ValueError("subject must be a dict!")

    now = datetime.now().timestamp()
    token_data = {
        "iat": now,
        "exp": now + exp,
        "type": token_type,
        "jti": str(uuid.uuid4()),
    }
    token_data.update(subject)

    token = jwt.encode(
        token_data,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )
    return token


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Expired signature')
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail='Invalid token')


def get_jti(token: str) -> str:
    payload = decode_token(token)
    return payload['jti']
