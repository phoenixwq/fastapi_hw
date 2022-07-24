from fastapi.security import OAuth2PasswordBearer
from fastapi import Security

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/login")


def get_token(token: str = Security(oauth2_scheme)):
    return token
