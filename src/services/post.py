import json
from functools import lru_cache
from typing import Optional

from fastapi import Depends
from sqlmodel import Session

from src.api.v1.schemas import PostCreate, PostModel
from src.db import AbstractCache, get_cache, get_session, CacheToken, get_refresh_cash
from src.models import Post
from src.services import ServiceMixin
import json
from functools import lru_cache
from typing import Optional

import jwt
from fastapi import Depends, HTTPException
from jwt import PyJWTError
from sqlmodel import Session
from starlette.status import HTTP_403_FORBIDDEN

from src.api.v1.schemas import PostCreate, PostModel
from src.core.config import JWT_SECRET_KEY, JWT_ALGORITHM
from src.db import AbstractCache, get_cache, get_session, get_access_cash
from src.models import Post
from src.services import ServiceMixin
__all__ = ("PostService", "get_post_service")

from src.services.auth import JWTAuth


class PostService(ServiceMixin):
    def __init__(self,
                 cache: AbstractCache,
                 access_cash: AbstractCache,
                 session: Session):
        super().__init__(cache=cache, session=session)
        self.auth = JWTAuth(access_cash, None)

    def get_post_list(self) -> dict:
        """Получить список постов."""
        posts = self.session.query(Post).order_by(Post.created_at).all()
        return {"posts": [PostModel(**post.dict()) for post in posts]}

    def get_post_detail(self, item_id: int) -> Optional[dict]:
        """Получить детальную информацию поста."""
        if cached_post := self.cache.get(key=f"{item_id}"):
            return json.loads(cached_post)

        post = self.session.query(Post).filter(Post.id == item_id).first()
        if post:
            self.cache.set(key=f"{post.id}", value=post.json())
        return post.dict() if post else None

    def create_post(self, post: PostCreate) -> dict:
        """Создать пост."""
        new_post = Post(title=post.title, description=post.description)
        self.session.add(new_post)
        self.session.commit()
        self.session.refresh(new_post)
        return new_post.dict()

    def check_token(self, token: str) -> None:
        try:
            payload = self.auth.decode_token(token)
            jti = payload["jti"]
        except PyJWTError:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
            )
        if self.auth.token_is_blocked(jti):
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Token was blocked"
            )

# get_post_service — это провайдер PostService. Синглтон
@lru_cache()
def get_post_service(
    cache: AbstractCache = Depends(get_cache),
    access_cash: AbstractCache = Depends(get_access_cash),
    session: Session = Depends(get_session),
) -> PostService:
    return PostService(cache=cache, session=session, access_cash=access_cash)
