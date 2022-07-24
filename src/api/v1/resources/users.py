from fastapi import status
from fastapi import APIRouter, Depends, HTTPException

from src.auth import get_token
from src.auth.schema import Token
from src.services.user import UserService, get_user_service
from src.api.v1.schemas.users import (
    UserLogin,
    UserUpdate,
    UserAbout,
    UserCreate
)

router = APIRouter()


@router.post(
    path="/signup",
    summary="Регистрация пользователя",
    tags=["users"],
    status_code=status.HTTP_201_CREATED,
)
def user_create(
        user: UserCreate,
        user_service: UserService = Depends(get_user_service),
) -> dict:
    try:
        new_user = user_service.create_user(user=user)
    except ValueError as error:
        raise {"error": str(error)}
    return {
        "msg": "User created.",
        "user": UserAbout(**new_user.dict())
    }


@router.post(
    path="/login",
    response_model=Token,
    summary="Авторизация пользователя",
    tags=["auth"],
)
def user_login(
        login_data: UserLogin,
        user_service: UserService = Depends(get_user_service)
) -> Token:
    return user_service.login_user(login_data=login_data)


@router.post(
    path="/refresh",
    response_model=Token,
    summary="Обновление токена",
    tags=["auth"],
)
def refresh(
        token: str = Depends(get_token),
        user_service: UserService = Depends(get_user_service)
):
    user = user_service.current_user(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    refresh_token = user_service.create_refresh_token(user.uuid)
    access_token = user_service.create_access_token(user.uuid)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post(
    path="/logout_all",
    summary="Выйти со всех устройств",
    tags=["users"]
)
def logout_all(
        user_service: UserService = Depends(get_user_service),
        token: str = Depends(get_token),
) -> dict:
    user_service.logout_all(token)
    return {"msg": "You have been logged out from all devices."}


@router.post(
    path="/logout",
    summary="Выйти",
    tags=["users"]
)
def logout(
        user_service: UserService = Depends(get_user_service),
        token: str = Depends(get_token),
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
        token: str = Depends(get_token),
) -> UserAbout:
    user = user_service.current_user(token)
    return UserAbout(**user.dict())


@router.patch(
    path='/users/me',
    status_code=200,
    tags=['users'],
)
def update_user(
        update_data: UserUpdate,
        user_service: UserService = Depends(get_user_service),
        token: str = Depends(get_token),
) -> dict:
    user = user_service.current_user(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    user = user_service.update_user(user, update_data.dict(exclude_unset=True))
    access_token = user_service.create_access_token(user.uuid)
    return {"msg": "Update", "user": UserAbout(**user.dict()), "access_token": access_token}
