from fastapi import status
from fastapi import APIRouter, Depends

from src.api.v1.schemas.auth import Token
from src.services.user import UserService, get_user_service
from src.api.v1.schemas.users import UserLogin, UserBase, UserUpdate, UserAbout, UserCreate
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()
reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/login")


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
        token: str = Depends(reusable_oauth2),
        user_service: UserService = Depends(get_user_service)
):
    tokens = user_service.refresh_token(token)
    return tokens


@router.post(
    path="/logout_all",
    summary="Выйти со всех устройств",
    tags=["users"]
)
def logout_all(
        user_service: UserService = Depends(get_user_service),
        token: str = Depends(reusable_oauth2),
) -> dict:
    """Signs out from all devices"""
    user_service.logout_all(token)
    return {"msg": "You have been logged out from all devices."}


@router.post(
    path="/logout",
    summary="Выйти",
    tags=["users"]
)
def logout(
        user_service: UserService = Depends(get_user_service),
        token: str = Depends(reusable_oauth2),
) -> dict:
    """Logging out of this device"""
    user_service.logout(token)
    return {"msg": "You have been logged out."}


@router.get(
    path='/users/me',
    status_code=200,
    tags=['users'],
)
def get_user(
        user_service: UserService = Depends(get_user_service),
        token: str = Depends(reusable_oauth2),
) -> UserBase:
    user = user_service.current_user(token)
    return UserBase(**user.dict())


@router.patch(
    path='/users/me',
    status_code=200,
    tags=['users'],
)
def update_user(
        update_data: UserUpdate,
        user_service: UserService = Depends(get_user_service),
        token: str = Depends(reusable_oauth2),
) -> dict:
    user = user_service.current_user(token)
    user, access_token = user_service.update_user(user, update_data.dict(exclude_unset=True))
    return {"msg": "Update", "user": UserAbout(**user.dict()), "access_token": access_token}


