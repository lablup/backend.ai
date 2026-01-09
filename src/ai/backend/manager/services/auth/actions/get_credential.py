from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.auth.types import CredentialData
from ai.backend.manager.services.auth.actions.base import AuthAction


@dataclass
class GetCredentialAction(AuthAction):
    """Action to get credential data by access key for authentication middleware."""

    access_key: str

    @override
    def entity_id(self) -> Optional[str]:
        return self.access_key

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_credential"


@dataclass
class GetCredentialActionResult(BaseActionResult):
    """Result containing credential data or None if not found."""

    credential: Optional[CredentialData]

    @override
    def entity_id(self) -> Optional[str]:
        return None
