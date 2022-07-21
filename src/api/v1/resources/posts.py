from http import HTTPStatus
from typing import Optional
from fastapi import HTTPException
from src.api.v1.schemas import PostCreate, PostListResponse, PostModel
from src.services import PostService, get_post_service
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()
reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/login")


@router.get(
    path="/",
    response_model=PostListResponse,
    summary="Список постов",
    tags=["posts"],
)
def post_list(
        post_service: PostService = Depends(get_post_service),
) -> PostListResponse:
    posts: dict = post_service.get_post_list()
    if not posts:
        # Если посты не найдены, отдаём 404 статус
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="posts not found")
    return PostListResponse(**posts)


@router.get(
    path="/{post_id}",
    response_model=PostModel,
    summary="Получить определенный пост",
    tags=["posts"],
)
def post_detail(
        post_id: int, post_service: PostService = Depends(get_post_service),
) -> PostModel:
    post: Optional[dict] = post_service.get_post_detail(item_id=post_id)
    if not post:
        # Если пост не найден, отдаём 404 статус
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="post not found")
    return PostModel(**post)


@router.post(
    path="/",
    response_model=PostModel,
    summary="Создать пост",
    tags=["posts"],
)
def post_create(
        post: PostCreate, post_service: PostService = Depends(get_post_service), token: str = Depends(reusable_oauth2),
) -> PostModel:
    post_service.check_token(token)
    post: dict = post_service.create_post(post=post)
    return PostModel(**post)
