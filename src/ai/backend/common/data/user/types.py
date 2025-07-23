from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class UserData:
    user_id: UUID
    is_authorized: bool
    is_admin: bool
    is_superadmin: bool
    role: str
    domain_name: str
