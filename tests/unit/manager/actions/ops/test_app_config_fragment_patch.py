"""Top-level key patch of an app config fragment, through the atomic upsert ops.

Runs against a real database: the patch is one ``INSERT .. ON CONFLICT DO UPDATE`` statement
whose result depends on the stored row.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Mapping, Sequence
from typing import Any

import pytest
import sqlalchemy as sa

from ai.backend.common.data.app_config.types import AppConfigScopeType
from ai.backend.common.data.entity.app_config_fragment import (
    AppConfigFragmentEntityType,
    AppConfigFragmentID,
)
from ai.backend.common.data.entity.domain import DomainEntityType, DomainID
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.errors.app_config import AppConfigFragmentWriteNotAllowed
from ai.backend.manager.models.app_config_allow_list.row import AppConfigAllowListRow
from ai.backend.manager.models.app_config_definition.row import AppConfigDefinitionRow
from ai.backend.manager.models.app_config_fragment.row import AppConfigFragmentRow
from ai.backend.manager.models.app_config_fragment.upserters import AppConfigFragmentPatchUpserter
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.services.app_config.actions.fragment.bulk_upsert import (
    BulkUpsertAppConfigFragmentsAction,
)
from ai.backend.manager.services.app_config.service import _merge_configs
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.ops_contract import Actor, Actors, OpsHarness, grant, provision

_ALLOWED = ("alpha", "beta")
_NOT_ALLOWED = "gamma"
_BASE = {"themeFamily": "default", "banner": {"text": "hi", "color": "red"}, "pinned": [1, 2]}


@pytest.fixture
async def fragment_db(
    ops_db: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine]:
    async with with_tables(
        ops_db, [AppConfigDefinitionRow, AppConfigAllowListRow, AppConfigFragmentRow]
    ):
        async with ops_db.begin_session() as sess:
            sess.add_all([
                AppConfigDefinitionRow(config_name=name) for name in (*_ALLOWED, _NOT_ALLOWED)
            ])
            await sess.flush()
            sess.add_all([
                AppConfigAllowListRow(
                    config_name=name,
                    scope_type=scope_type,
                    rank=scope_type.default_rank(),
                )
                for name in _ALLOWED
                for scope_type in (AppConfigScopeType.PUBLIC, AppConfigScopeType.DOMAIN)
            ])
            await sess.commit()
        yield ops_db


@pytest.fixture
async def owner(fragment_db: ExtendedAsyncSAEngine, actors: Actors) -> DomainID:
    await grant(
        fragment_db,
        actors.user_id(Actor.GRANTED),
        DomainEntityType(),
        actors.domain_id,
        AppConfigFragmentEntityType(),
        Permission.CREATE | Permission.UPDATE,
    )
    return actors.domain_id


def _patch(
    owner: DomainID,
    config_name: str,
    set_values: Mapping[str, Any] | None = None,
    unset: Sequence[str] = (),
) -> AppConfigFragmentPatchUpserter:
    return AppConfigFragmentPatchUpserter(
        config_name=config_name, owner=owner, config=dict(set_values or {}), unset=unset
    )


def _processor(harness: OpsHarness) -> Any:
    return harness.group(AppConfigFragmentEntityType()).entity_atomic_upsert_ops(
        BulkUpsertAppConfigFragmentsAction
    )


async def _run(
    harness: OpsHarness,
    actors: Actors,
    owner: DomainID,
    *patches: AppConfigFragmentPatchUpserter,
) -> Any:
    with actors.acting_as(Actor.GRANTED):
        return await _processor(harness).run(
            BulkUpsertAppConfigFragmentsAction(owner=owner, upserters=list(patches))
        )


async def _stored(
    db: ExtendedAsyncSAEngine, scope_type: AppConfigScopeType = AppConfigScopeType.DOMAIN
) -> dict[str, dict[str, Any]]:
    async with db.begin_readonly_session() as sess:
        rows = (
            await sess.scalars(
                sa.select(AppConfigFragmentRow).where(AppConfigFragmentRow.scope_type == scope_type)
            )
        ).all()
    return {row.config_name: row.config for row in rows}


async def _seed(
    db: ExtendedAsyncSAEngine,
    owner: DomainID | None,
    name: str,
    config: dict[str, Any],
) -> AppConfigFragmentID:
    async with db.begin_session() as sess:
        row = AppConfigFragmentRow(
            config_name=name,
            scope_type=AppConfigScopeType.of_owner(owner),
            scope_id=owner,
            config=config,
        )
        sess.add(row)
        await sess.flush()
        fragment_id = AppConfigFragmentID(row.id)
        await sess.commit()
    if owner is not None:
        await provision(
            db, AppConfigFragmentEntityType(), fragment_id, [(DomainEntityType(), owner)]
        )
    return fragment_id


class TestSet:
    async def test_setting_a_key_leaves_the_other_keys_as_they_were(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        owner: DomainID,
    ) -> None:
        existing = await _seed(fragment_db, owner, "alpha", _BASE)

        result = await _run(harness, actors, owner, _patch(owner, "alpha", {"themeFamily": "dark"}))

        assert (await _stored(fragment_db))["alpha"] == {**_BASE, "themeFamily": "dark"}
        assert [item.id for item in result.items] == [existing]
        assert result.items[0].config == {**_BASE, "themeFamily": "dark"}

    async def test_a_value_replaces_the_whole_value_of_its_key(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        owner: DomainID,
    ) -> None:
        await _seed(fragment_db, owner, "alpha", _BASE)

        await _run(harness, actors, owner, _patch(owner, "alpha", {"banner": {"text": "bye"}}))

        assert (await _stored(fragment_db))["alpha"]["banner"] == {"text": "bye"}

    async def test_a_key_with_a_dot_is_a_key_not_a_path(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        owner: DomainID,
    ) -> None:
        await _seed(fragment_db, owner, "alpha", {"a": {"b": 1}})

        await _run(harness, actors, owner, _patch(owner, "alpha", {"a.b": 2}))

        assert (await _stored(fragment_db))["alpha"] == {"a": {"b": 1}, "a.b": 2}

    async def test_a_missing_fragment_is_created_with_the_keys_set(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        owner: DomainID,
    ) -> None:
        await _run(harness, actors, owner, _patch(owner, "alpha", {"themeFamily": "dark"}))

        assert await _stored(fragment_db) == {"alpha": {"themeFamily": "dark"}}


class TestUnset:
    async def test_unsetting_a_key_removes_only_that_key(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        owner: DomainID,
    ) -> None:
        await _seed(fragment_db, owner, "alpha", _BASE)

        await _run(harness, actors, owner, _patch(owner, "alpha", unset=["themeFamily"]))

        assert (await _stored(fragment_db))["alpha"] == {
            "banner": _BASE["banner"],
            "pinned": _BASE["pinned"],
        }

    async def test_unsetting_an_absent_key_changes_nothing(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        owner: DomainID,
    ) -> None:
        await _seed(fragment_db, owner, "alpha", _BASE)

        await _run(harness, actors, owner, _patch(owner, "alpha", unset=["nope"]))

        assert (await _stored(fragment_db))["alpha"] == _BASE

    async def test_set_and_unset_apply_in_one_patch(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        owner: DomainID,
    ) -> None:
        await _seed(fragment_db, owner, "alpha", _BASE)

        await _run(
            harness,
            actors,
            owner,
            _patch(owner, "alpha", {"themeFamily": "dark"}, unset=["pinned"]),
        )

        assert (await _stored(fragment_db))["alpha"] == {
            "themeFamily": "dark",
            "banner": _BASE["banner"],
        }

    async def test_the_lower_scope_value_shows_again_after_the_unset(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        owner: DomainID,
    ) -> None:
        """The merge reads the stored fragments rank by rank: the higher scope here is the
        domain and the lower one public, standing for user over domain."""
        await _seed(fragment_db, None, "alpha", {"themeFamily": "public"})
        await _seed(fragment_db, owner, "alpha", {"themeFamily": "domain", "extra": 1})

        before = _merge_configs(await _fragments_by_rank(fragment_db))
        await _run(harness, actors, owner, _patch(owner, "alpha", unset=["themeFamily"]))
        after = _merge_configs(await _fragments_by_rank(fragment_db))

        assert before == {"themeFamily": "domain", "extra": 1}
        assert after == {"themeFamily": "public", "extra": 1}


async def _fragments_by_rank(db: ExtendedAsyncSAEngine) -> list[Any]:
    async with db.begin_readonly_session() as sess:
        rows = (
            await sess.scalars(
                sa.select(AppConfigFragmentRow)
                .join(
                    AppConfigAllowListRow,
                    sa.and_(
                        AppConfigAllowListRow.config_name == AppConfigFragmentRow.config_name,
                        AppConfigAllowListRow.scope_type == AppConfigFragmentRow.scope_type,
                    ),
                )
                .order_by(AppConfigAllowListRow.rank)
            )
        ).all()
        return [row.to_data() for row in rows]


class TestConcurrency:
    async def test_patches_of_different_keys_both_land(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        owner: DomainID,
    ) -> None:
        await _seed(fragment_db, owner, "alpha", {"base": 0})

        await asyncio.gather(
            _run(harness, actors, owner, _patch(owner, "alpha", {"themeFamily": "dark"})),
            _run(harness, actors, owner, _patch(owner, "alpha", {"banner": {"text": "hi"}})),
        )

        assert (await _stored(fragment_db))["alpha"] == {
            "base": 0,
            "themeFamily": "dark",
            "banner": {"text": "hi"},
        }

    async def test_a_set_and_an_unset_of_different_keys_both_land(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        owner: DomainID,
    ) -> None:
        await _seed(fragment_db, owner, "alpha", {"base": 0, "gone": 1})

        await asyncio.gather(
            _run(harness, actors, owner, _patch(owner, "alpha", {"themeFamily": "dark"})),
            _run(harness, actors, owner, _patch(owner, "alpha", unset=["gone"])),
        )

        assert (await _stored(fragment_db))["alpha"] == {"base": 0, "themeFamily": "dark"}


class TestWriteGate:
    async def test_a_config_the_allow_list_does_not_allow_is_refused(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        owner: DomainID,
    ) -> None:
        with pytest.raises(AppConfigFragmentWriteNotAllowed):
            await _run(harness, actors, owner, _patch(owner, _NOT_ALLOWED, {"k": 1}))

        assert await _stored(fragment_db) == {}

    async def test_a_refused_item_undoes_every_item(
        self,
        fragment_db: ExtendedAsyncSAEngine,
        harness: OpsHarness,
        actors: Actors,
        owner: DomainID,
    ) -> None:
        await _seed(fragment_db, owner, "alpha", _BASE)

        with pytest.raises(AppConfigFragmentWriteNotAllowed):
            await _run(
                harness,
                actors,
                owner,
                _patch(owner, "alpha", {"themeFamily": "dark"}),
                _patch(owner, _NOT_ALLOWED, {"k": 1}),
            )

        assert await _stored(fragment_db) == {"alpha": _BASE}
