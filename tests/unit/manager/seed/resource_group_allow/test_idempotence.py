"""Applying the kind again changes nothing."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path

import pytest

from ai.backend.manager.seed.types import SeedKind


@pytest.mark.parametrize(
    "kind_name",
    [
        SeedKind.RESOURCE_GROUP_FOR_DOMAIN,
        SeedKind.RESOURCE_GROUP_FOR_PROJECT,
        SeedKind.RESOURCE_GROUP_FOR_KEYPAIR,
    ],
)
async def test_applying_again_changes_nothing(
    kind_name: SeedKind,
    assert_idempotent: Callable[[SeedKind, Path], Awaitable[None]],
    resource_group_allow_seed_dir: Path,
) -> None:
    await assert_idempotent(kind_name, resource_group_allow_seed_dir)
