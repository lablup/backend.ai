import uuid
from dataclasses import dataclass

from ai.backend.manager.models.user import UserRole
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


@dataclass
class ClientContext:
    db: ExtendedAsyncSAEngine

    domain_name: str
    user_id: uuid.UUID
    user_role: UserRole
