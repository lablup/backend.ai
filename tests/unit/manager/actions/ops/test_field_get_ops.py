"""``get_ops (field)``: reading one field row, with an artifact's revision as the
representative."""

from __future__ import annotations

import contextlib
import uuid
from collections.abc import AsyncGenerator, Callable
from typing import Any

import pytest

from ai.backend.common.data.entity.artifact import ArtifactEntityType, ArtifactID
from ai.backend.common.data.entity.artifact_revision import (
    ArtifactRevisionFieldType,
    ArtifactRevisionID,
)
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.exception import BackendAIError
from ai.backend.manager.actions.registry.types import FieldGroupMeta
from ai.backend.manager.actions.types import ActionOperationType, OperationStatus
from ai.backend.manager.data.artifact.types import ArtifactRevisionData, ArtifactType
from ai.backend.manager.errors.base.field import FieldNotFoundError
from ai.backend.manager.errors.common import GenericBadRequest
from ai.backend.manager.models.artifact.row import ArtifactRow
from ai.backend.manager.models.artifact_registries.row import ArtifactRegistryRow
from ai.backend.manager.models.artifact_revision.row import ArtifactRevisionRow
from ai.backend.manager.models.huggingface_registry.row import HuggingFaceRegistryRow
from ai.backend.manager.models.reservoir_registry.row import ReservoirRegistryRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.rbac.permission_check_repository import (
    RbacPermissionCheckRepository,
)
from ai.backend.manager.services.artifact.revision.actions.get import GetArtifactRevisionAction
from ai.backend.manager.services.artifact.revision.actions.lookup_owner import (
    LookupArtifactRevisionOwnerAction,
    LookupBulkArtifactRevisionOwnerAction,
)
from ai.backend.testutils.db import with_tables
from ai.backend.testutils.ops_contract import (
    ANONYMOUS_NOT_REFUSED,
    MONITOR_READ_REFUSED,
    Actor,
    Actors,
    AuditRecord,
    OpsHarness,
    assert_refused,
    entity_key,
    grant,
    provision,
)

_OWNER_LOOKUP = LookupArtifactRevisionOwnerAction.action_name()
_OPERATION = GetArtifactRevisionAction.action_name()


@pytest.fixture
async def artifact_db(
    ops_db: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(
        ops_db,
        [
            ArtifactRegistryRow,
            HuggingFaceRegistryRow,
            ReservoirRegistryRow,
            ArtifactRow,
            ArtifactRevisionRow,
        ],
    ):
        yield ops_db


@pytest.fixture
async def artifact(artifact_db: ExtendedAsyncSAEngine, actors: Actors) -> ArtifactID:
    artifact_id = ArtifactID(uuid.uuid4())
    async with artifact_db.begin_session() as sess:
        sess.add(
            ArtifactRow(
                id=artifact_id,
                type=ArtifactType.MODEL,
                name=f"model-{artifact_id.hex[:8]}",
                registry_id=uuid.uuid4(),
                registry_type="huggingface",
                source_registry_id=uuid.uuid4(),
                source_registry_type="huggingface",
            )
        )
        await sess.commit()
    await provision(artifact_db, ArtifactEntityType(), artifact_id)
    await grant(
        artifact_db,
        actors.user_id(Actor.GRANTED),
        ArtifactEntityType(),
        artifact_id,
        ArtifactEntityType(),
        Permission.READ,
    )
    return artifact_id


@pytest.fixture
async def revision(artifact_db: ExtendedAsyncSAEngine, artifact: ArtifactID) -> ArtifactRevisionID:
    async with artifact_db.begin_session() as sess:
        row = ArtifactRevisionRow(artifact_id=artifact, version="1.0.0")
        sess.add(row)
        await sess.flush()
        revision_id = row.id
        await sess.commit()
    return revision_id


def _processor(harness: OpsHarness) -> Any:
    revisions = harness.group(ArtifactEntityType()).field_group(
        FieldGroupMeta(ArtifactRevisionFieldType()),
        ArtifactRevisionData,
        LookupArtifactRevisionOwnerAction,
        LookupBulkArtifactRevisionOwnerAction,
    )
    return revisions.get_ops(GetArtifactRevisionAction)


def _get(revision_id: ArtifactRevisionID) -> GetArtifactRevisionAction:
    return GetArtifactRevisionAction(artifact_revision_id=revision_id)


def _rows(
    records: list[AuditRecord],
) -> list[tuple[tuple[str | None, str | None], str, OperationStatus]]:
    return [((r.entity_type, r.entity_id), r.operation, r.status) for r in records]


class TestActor:
    @pytest.mark.parametrize(
        ("actor", "enforced"),
        [
            pytest.param(Actor.SUPERADMIN, True, id="actor-2"),
            pytest.param(Actor.GRANTED, True, id="actor-3"),
            pytest.param(Actor.MONITOR, True, id="actor-5", marks=MONITOR_READ_REFUSED),
            pytest.param(Actor.UNGRANTED, False, id="actor-6"),
        ],
    )
    async def test_the_row_is_read(
        self,
        harness: OpsHarness,
        actors: Actors,
        revision: ArtifactRevisionID,
        actor: Actor,
        enforced: bool,
    ) -> None:
        harness.enforce(enforced)

        with actors.acting_as(actor):
            result = await _processor(harness).run(_get(revision))

        assert result.data.id == revision

    @pytest.mark.parametrize(
        ("actor", "error"),
        [
            pytest.param(
                Actor.ANONYMOUS, BackendAIError, id="actor-1", marks=ANONYMOUS_NOT_REFUSED
            ),
            pytest.param(Actor.UNGRANTED, GenericBadRequest, id="actor-4"),
        ],
    )
    async def test_the_read_is_refused(
        self,
        harness: OpsHarness,
        actors: Actors,
        revision: ArtifactRevisionID,
        repository_calls: Callable[[str], list[Any]],
        actor: Actor,
        error: type[Exception],
    ) -> None:
        reads = repository_calls("get_field")

        with actors.acting_as(actor):
            with pytest.raises(error) as raised:
                await _processor(harness).run(_get(revision))

        assert reads == []
        assert await harness.audit(_OPERATION) == []
        if actor is Actor.ANONYMOUS:
            assert_refused(raised.value)


class TestTarget:
    @pytest.mark.parametrize(
        ("actor", "error"),
        [
            pytest.param(Actor.GRANTED, GenericBadRequest, id="target-1"),
            pytest.param(Actor.SUPERADMIN, FieldNotFoundError, id="target-2"),
        ],
    )
    async def test_missing(
        self,
        harness: OpsHarness,
        actors: Actors,
        artifact: ArtifactID,
        actor: Actor,
        error: type[Exception],
    ) -> None:
        with actors.acting_as(actor):
            with pytest.raises(error):
                await _processor(harness).run(_get(ArtifactRevisionID(uuid.uuid4())))

    @pytest.mark.parametrize(
        "exists", [pytest.param(False, id="missing"), pytest.param(True, id="denied")]
    )
    async def test_the_refusal_names_neither_the_row_nor_its_owner(
        self,
        harness: OpsHarness,
        actors: Actors,
        artifact: ArtifactID,
        revision: ArtifactRevisionID,
        exists: bool,
    ) -> None:
        """target-3."""
        target = revision if exists else ArtifactRevisionID(uuid.uuid4())

        with actors.acting_as(Actor.UNGRANTED):
            with pytest.raises(GenericBadRequest) as caught:
                await _processor(harness).run(_get(target))

        assert str(target) not in str(caught.value)
        assert str(artifact) not in str(caught.value)


class TestRecord:
    @pytest.mark.parametrize(
        "record_reads",
        [pytest.param(True, id="record-1"), pytest.param(False, id="record-1-reads-unrecorded")],
    )
    async def test_success(
        self,
        artifact_db: ExtendedAsyncSAEngine,
        actors: Actors,
        artifact: ArtifactID,
        revision: ArtifactRevisionID,
        record_reads: bool,
    ) -> None:
        harness = OpsHarness(artifact_db, record_reads=record_reads)

        with actors.acting_as(Actor.GRANTED):
            await _processor(harness).run(_get(revision))

        lookup = (entity_key(artifact), ActionOperationType.LOOKUP, OperationStatus.SUCCESS)
        operation = (entity_key(artifact), ActionOperationType.GET, OperationStatus.SUCCESS)
        assert _rows(await harness.audit(_OWNER_LOOKUP)) == ([lookup] if record_reads else [])
        assert _rows(await harness.audit(_OPERATION)) == ([operation] if record_reads else [])

    async def test_a_denied_owner_lookup_leaves_no_operation_row(
        self,
        silent_reads_harness: OpsHarness,
        actors: Actors,
        artifact: ArtifactID,
        revision: ArtifactRevisionID,
    ) -> None:
        """record-2."""
        with actors.acting_as(Actor.UNGRANTED):
            with contextlib.suppress(Exception):
                await _processor(silent_reads_harness).run(_get(revision))

        assert _rows(await silent_reads_harness.audit(_OWNER_LOOKUP)) == [
            (entity_key(artifact), ActionOperationType.LOOKUP, OperationStatus.DENIED)
        ]
        assert await silent_reads_harness.audit(_OPERATION) == []

    async def test_a_missing_row_is_a_lookup_error_by_its_key(
        self, harness: OpsHarness, actors: Actors, artifact: ArtifactID
    ) -> None:
        """record-3."""
        missing = ArtifactRevisionID(uuid.uuid4())

        with actors.acting_as(Actor.SUPERADMIN):
            with contextlib.suppress(Exception):
                await _processor(harness).run(_get(missing))

        lookups = await harness.audit(_OWNER_LOOKUP)
        assert [(r.entity_id, r.status, r.lookup_key) for r in lookups] == [
            (None, OperationStatus.ERROR, f"id={missing}")
        ]
        assert await harness.audit(_OPERATION) == []

    async def test_a_failing_permission_read_is_an_error_not_a_denial(
        self,
        harness: OpsHarness,
        actors: Actors,
        revision: ArtifactRevisionID,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """record-4."""

        async def broken(*_: Any, **__: Any) -> Any:
            raise RuntimeError("the permission read failed")

        monkeypatch.setattr(RbacPermissionCheckRepository, "owned_permissions", broken)

        with actors.acting_as(Actor.GRANTED):
            with pytest.raises(RuntimeError):
                await _processor(harness).run(_get(revision))

        assert [r.status for r in await harness.audit(_OWNER_LOOKUP)] == [OperationStatus.ERROR]
        assert await harness.audit(_OPERATION) == []


class TestResult:
    async def test_the_data_is_the_row(
        self,
        harness: OpsHarness,
        actors: Actors,
        artifact: ArtifactID,
        revision: ArtifactRevisionID,
    ) -> None:
        """result-1."""
        with actors.acting_as(Actor.GRANTED):
            result = await _processor(harness).run(_get(revision))

        assert (result.data.id, result.data.artifact_id, result.data.version) == (
            revision,
            artifact,
            "1.0.0",
        )
