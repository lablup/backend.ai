import uuid
from dataclasses import dataclass

from ..user import UserRole
from ..utils import ExtendedAsyncSAEngine


@dataclass
class ClientContext:
    db: ExtendedAsyncSAEngine

    domain_name: str
    user_id: uuid.UUID
    user_role: UserRole
