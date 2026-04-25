"""Bulk-mutation service-layer dataclasses for app_config_policies (BEP-1052 §3)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfigPolicyBulkItem:
    """One item for `adminBulkCreate/Update` — config_name + scope chain.

    `user_writable` was dropped pre-landing — user writes are blocked
    entirely in this iteration; re-introduce when user writes are
    enabled (BEP-1052 §1).
    """

    config_name: str
    scope_sources: Sequence[str]


@dataclass(frozen=True)
class AppConfigPolicyBulkItemError:
    """Per-item failure carried through bulk policy action results."""

    index: int
    config_name: str
    message: str
