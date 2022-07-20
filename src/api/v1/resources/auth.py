from fastapi import status
from src.api.v1.schemas.auth import Token
from src.api.v1.schemas.users import UserLogin
from src.services.user import UserService, get_user_service
from fastapi import APIRouter, Depends, Security
from src.api.v1.schemas.users import UserCreate
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

router = APIRouter()
security = HTTPBearer()


@router.post(
    path="/signup",
    summary="Регистрация пользователя",
    tags=["users"],
    status_code=status.HTTP_201_CREATED,
)
def user_signup(
        user: UserCreate,
        user_service: UserService = Depends(get_user_service),
) -> dict:
    try:
        res = user_service.create_user(user=user)
    except ValueError as error:
        return {"msg": str(error)}
    return res


@router.post(
    path="/login",
    response_model=Token,
    summary="Авторизация пользователя",
    tags=["auth"],
)
def login(
        login_data: UserLogin,
        user_service: UserService = Depends(get_user_service)
) -> Token:
    token = user_service.login_user(login_data=login_data)
    return token


@router.post(
    path="/refresh",
    response_model=Token,
    summary="Обновление токена",
    tags=["auth"],
)
def refresh(
        credentials: HTTPAuthorizationCredentials = Security(security),
        user_service: UserService = Depends(get_user_service)
):
    expired_token = credentials.credentials
    tokens = user_service.refresh_token(expired_token)
    return tokens
