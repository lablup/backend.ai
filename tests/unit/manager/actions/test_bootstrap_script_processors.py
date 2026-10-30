"""Bootstrap script operations named by id, answered for by the user the row is set on."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa

from ai.backend.common.data.entity.bootstrap_script import (
    BootstrapScript,
    BootstrapScriptFieldType,
    BootstrapScriptID,
)
from ai.backend.common.data.entity.user import UserEntityType, UserID
from ai.backend.common.data.permission.types import Permission
from ai.backend.manager.actions.registry.types import FieldGroupMeta
from ai.backend.manager.data.bootstrap_script.types import BootstrapScriptData
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.models.bootstrap_script.row import (
    BootstrapScriptRow,
    UserDefaultBootstrapScriptRow,
)
from ai.backend.manager.models.bootstrap_script_revision.creators import (
    BootstrapScriptRevisionCreator,
)
from ai.backend.manager.models.bootstrap_script_revision.row import BootstrapScriptRevisionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.resource_policy.provider import (
    ResourcePolicyOpsProvider,
)
from ai.backend.manager.repositories.ops.v2.share.provider import ShareOpsProvider
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.services.user.bootstrap_script.actions.add_revision import (
    AddBootstrapScriptRevisionAction,
)
from ai.backend.manager.services.user.bootstrap_script.actions.get import GetBootstrapScriptAction
from ai.backend.manager.services.user.bootstrap_script.actions.lookup_owner import (
    LookupBootstrapScriptOwnerAction,
    LookupBulkBootstrapScriptOwnerAction,
)
from ai.backend.manager.services.user.bootstrap_script.actions.purge import (
    PurgeBootstrapScriptAction,
)
from ai.backend.manager.services.user.bootstrap_script.processors import BootstrapScriptProcessors
from ai.backend.manager.services.user.service import UserService
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.ops_contract import (
    BASE_TABLES,
    Actor,
    Actors,
    OpsHarness,
    grant,
    seed_actors,
)


@pytest.fixture
async def ops_db(
    global_entity_ids: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(
        global_entity_ids,
        [
            *BASE_TABLES,
            BootstrapScriptRow,
            UserDefaultBootstrapScriptRow,
            BootstrapScriptRevisionRow,
        ],
    ):
        yield global_entity_ids


@pytest.fixture
async def actors(ops_db: ExtendedAsyncSAEngine) -> Actors:
    actors = await seed_actors(ops_db)
    owner = actors.user_id(Actor.GRANTED)
    await grant(
        ops_db,
        owner,
        UserEntityType(),
        owner,
        UserEntityType(),
        Permission.READ | Permission.UPDATE,
    )
    return actors


@pytest.fixture
def processors(ops_db: ExtendedAsyncSAEngine) -> BootstrapScriptProcessors:
    harness = OpsHarness(ops_db)
    repository = UserRepository(
        db=ops_db,
        v2_ops_provider=V2DBOpsProvider(ops_db),
        share_ops_provider=ShareOpsProvider(ops_db),
        policy_ops_provider=ResourcePolicyOpsProvider(ops_db),
        key_provider_pool=KeyProviderPool(providers=[], write_provider_type=KeyProviderType.PLAIN),
    )
    service = UserService(MagicMock(), MagicMock(), MagicMock(), repository, MagicMock())
    return BootstrapScriptProcessors(
        harness.group(UserEntityType()),
        harness.registry.dangling_lookup_field_group(
            FieldGroupMeta(BootstrapScriptFieldType()),
            BootstrapScriptData,
            LookupBootstrapScriptOwnerAction,
            LookupBulkBootstrapScriptOwnerAction,
        ),
        service,
    )


async def _seed_script(db: ExtendedAsyncSAEngine, owner: UserID) -> BootstrapScriptID:
    async with db.begin_session() as sess:
        row = BootstrapScriptRow(entity_type=UserEntityType(), entity_id=owner)
        sess.add(row)
        await sess.flush()
        sess.add(
            BootstrapScriptRevisionRow(
                script_id=row.id, revision_number=1, script=BootstrapScript("echo 1")
            )
        )
        return row.id


@pytest.fixture
async def own_script(ops_db: ExtendedAsyncSAEngine, actors: Actors) -> BootstrapScriptID:
    return await _seed_script(ops_db, actors.user_id(Actor.GRANTED))


@pytest.fixture
async def other_script(ops_db: ExtendedAsyncSAEngine, actors: Actors) -> BootstrapScriptID:
    return await _seed_script(ops_db, actors.user_id(Actor.UNGRANTED))


async def _script_exists(db: ExtendedAsyncSAEngine, script_id: BootstrapScriptID) -> bool:
    async with db.begin_readonly_session() as sess:
        found = await sess.scalar(
            sa.select(BootstrapScriptRow.id).where(BootstrapScriptRow.id == script_id)
        )
    return found is not None


class TestOwnScript:
    async def test_get(
        self,
        processors: BootstrapScriptProcessors,
        actors: Actors,
        own_script: BootstrapScriptID,
    ) -> None:
        with actors.acting_as(Actor.GRANTED):
            result = await processors.get.run(GetBootstrapScriptAction(script_id=own_script))

        assert result.data.id == own_script

    async def test_add_revision(
        self,
        processors: BootstrapScriptProcessors,
        actors: Actors,
        own_script: BootstrapScriptID,
    ) -> None:
        owner = actors.user_id(Actor.GRANTED)
        with actors.acting_as(Actor.GRANTED):
            result = await processors.add_revision.run(
                AddBootstrapScriptRevisionAction(
                    creator=BootstrapScriptRevisionCreator(
                        script_id=own_script, script=BootstrapScript("echo 2"), creator_id=owner
                    )
                )
            )

        assert (result.revision.revision_number, result.revision.script) == (2, "echo 2")

    async def test_purge(
        self,
        ops_db: ExtendedAsyncSAEngine,
        processors: BootstrapScriptProcessors,
        actors: Actors,
        own_script: BootstrapScriptID,
    ) -> None:
        with actors.acting_as(Actor.GRANTED):
            await processors.purge.run(PurgeBootstrapScriptAction(script_id=own_script))

        assert not await _script_exists(ops_db, own_script)


class TestOtherUsersScript:
    async def test_get_is_refused(
        self,
        processors: BootstrapScriptProcessors,
        actors: Actors,
        other_script: BootstrapScriptID,
    ) -> None:
        """The owner lookup answers a denial as it answers a missing row."""
        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(GenericBadRequest):
                await processors.get.run(GetBootstrapScriptAction(script_id=other_script))
