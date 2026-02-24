from __future__ import annotations

from dataclasses import dataclass

from ai.backend.manager.data.resource.types import KeyPairResourcePolicyData

__all__ = ("KeypairResourcePolicySearchResult",)


@dataclass
class KeypairResourcePolicySearchResult:
    """Result from searching keypair resource policies."""

    items: list[KeyPairResourcePolicyData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
