from sqlmodel import Session

from src.db import AbstractCache


class ServiceMixin:
    def __init__(self, cache: AbstractCache, session: Session):
        self.cache: AbstractCache = cache
        self.session: Session = session
