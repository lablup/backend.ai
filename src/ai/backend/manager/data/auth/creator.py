from dataclasses import dataclass
from typing import Any, Optional, override

from ai.backend.manager.types import Creator


@dataclass
class AuthCreator(Creator):
    """Creator for authentication-related operations."""

    # Add fields based on authentication needs
    user_id: str
    domain_name: str
    is_active: bool = True

    @override
    def fields_to_store(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "domain_name": self.domain_name,
            "is_active": self.is_active,
        }


@dataclass
class SSHKeypairCreator(Creator):
    """Creator for SSH keypair operations."""

    user_id: str
    public_key: str
    private_key: Optional[str] = None
    name: Optional[str] = None

    @override
    def fields_to_store(self) -> dict[str, Any]:
        to_store = {
            "user_id": self.user_id,
            "public_key": self.public_key,
        }
        if self.private_key is not None:
            to_store["private_key"] = self.private_key
        if self.name is not None:
            to_store["name"] = self.name
        return to_store
