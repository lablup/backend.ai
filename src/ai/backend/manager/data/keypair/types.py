from dataclasses import dataclass


@dataclass
class KeyPairCreator:
    is_active: bool
    is_admin: bool
    resource_policy: str
    rate_limit: int
