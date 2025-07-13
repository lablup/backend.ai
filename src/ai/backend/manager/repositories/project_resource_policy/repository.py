from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class ProjectResourcePolicyRepository:
    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db
