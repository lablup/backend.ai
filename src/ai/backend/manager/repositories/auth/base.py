from abc import ABC

from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class BaseAuthRepository(ABC):
    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db
