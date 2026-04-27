from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class AppConfigPolicyData:
    id: uuid.UUID
    config_name: str
    scope_sources: Sequence[str]
    created_at: datetime
    updated_at: datetime | None


@dataclass(frozen=True)
class AppConfigPolicyBulkCreateItem:
    """One item for `adminBulkCreateAppConfigPolicies` — new policy
    name + scope chain."""

    config_name: str
    scope_sources: Sequence[str]


@dataclass(frozen=True)
class AppConfigPolicyBulkUpdateItem:
    """One item for `adminBulkUpdateAppConfigPolicies` — target row id
    + new scope chain. `config_name` is immutable, so it's not part of
    the update payload."""

    id: uuid.UUID
    scope_sources: Sequence[str]


@dataclass(frozen=True)
class AppConfigPolicyBulkItemError:
    """Per-item failure carried through bulk policy action results."""

    index: int
    message: str
