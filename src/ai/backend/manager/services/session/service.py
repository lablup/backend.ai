from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class SessionService:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db
