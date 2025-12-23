from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class CredentialsByAccessKey:
    """Credentials fetched by access key from database."""

    # Both fields may not be the same as UserRow and KeypairRow; they are just named with legacy usage
    # TODO: Refactor to use proper types
    user_row: Optional[dict[str, Any]]
    keypair_row: Optional[dict[str, Any]]
