"""Bulk-mutation service-layer dataclasses for app_config_fragments."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentKey


@dataclass(frozen=True)
class AppConfigFragmentBulkItem:
    """One item for `adminBulkCreate/Update` — natural key + payload."""

    key: AppConfigFragmentKey
    config: Mapping[str, Any]


@dataclass(frozen=True)
class MyAppConfigFragmentBulkItem:
    """One item for `bulkCreate/UpdateMy` — `name` + payload.

    `scope_type` is always `USER` and `scope_id` is resolved from the
    current user at the adapter layer.
    """

    name: str
    config: Mapping[str, Any]


@dataclass(frozen=True)
class AppConfigFragmentBulkItemError:
    """Per-item failure carried through bulk action results.

    `scope_type` / `scope_id` / `name` identify which input row failed;
    `index` preserves the caller's original list position.
    """

    index: int
    scope_type: str
    scope_id: str
    name: str
    message: str
