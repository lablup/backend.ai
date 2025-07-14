from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


class AdminVfolderRepository:
    """
    Repository for admin-specific vfolder operations that bypass ownership checks.
    This should only be used by superadmin users.
    """

    _db: ExtendedAsyncSAEngine

    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self._db = db
