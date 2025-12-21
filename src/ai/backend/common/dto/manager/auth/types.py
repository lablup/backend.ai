from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class CredentialsByAccessKey:
    """Credentials fetched by access key from database."""

    # Both fields can be not same as UserRow, KeypairRow, just named with legacy usage
    # TODO: Refactor to use proper types
    user_row: Optional[dict[str, Any]]
    keypair_row: Optional[dict[str, Any]]
