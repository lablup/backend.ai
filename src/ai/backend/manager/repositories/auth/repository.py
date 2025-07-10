from ai.backend.manager.models.utils import ExtendedAsyncSAEngine

from .keypair_repository import KeypairRepository
from .user_repository import UserRepository


class AuthRepository:
    def __init__(self, db: ExtendedAsyncSAEngine) -> None:
        self.user = UserRepository(db)
        self.keypair = KeypairRepository(db)
