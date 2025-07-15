from dataclasses import dataclass
from typing import Any, Optional, override
from uuid import UUID

from ai.backend.manager.types import Creator


@dataclass
class KeyPairCreator(Creator):
    """Creator for keypair operations."""
    
    access_key: str
    secret_key: str
    user: UUID
    is_active: bool = True
    is_admin: bool = False
    resource_policy: str = "default"
    rate_limit: int = 1000
    num_queries: int = 0
    ssh_public_key: Optional[str] = None
    bootstrap_script: Optional[str] = None
    
    @override
    def fields_to_store(self) -> dict[str, Any]:
        to_store = {
            "access_key": self.access_key,
            "secret_key": self.secret_key,
            "user": self.user,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "resource_policy": self.resource_policy,
            "rate_limit": self.rate_limit,
            "num_queries": self.num_queries,
        }
        if self.ssh_public_key is not None:
            to_store["ssh_public_key"] = self.ssh_public_key
        if self.bootstrap_script is not None:
            to_store["bootstrap_script"] = self.bootstrap_script
        return to_store