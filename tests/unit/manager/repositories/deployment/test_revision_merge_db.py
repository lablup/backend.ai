"""DB-backed verification of the BA-5983 revision merge contract.

Each test class seeds one specific ``RuntimeVariantRow.default_model_definition``
shape into the DB (so it round-trips through ``PydanticColumn``
serialization) and runs the production ``RevisionDraftReader`` +
``RevisionDraft.merge`` pipeline against various request inputs. The
parametrize tables only carry the request ``ModelDefinitionInput`` and
the expected resolved values — the DB baseline is fixed per class via
its ``variant_id`` fixture.

Scenarios are partitioned by baseline shape so each class makes the
"what's in the DB" / "what the user sends" / "what should come out"
relationship obvious at a glance.
"""

from __future__ import annotations

import functools
import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from ai.backend.common.config import (
    ModelConfigDraft,
    ModelDefinitionDraft,
    ModelHealthCheckDraft,
    ModelServiceConfigDraft,
)
from ai.backend.common.dto.manager.v2.deployment.request import (
    ModelConfigInput,
    ModelDefinitionInput,
    ModelHealthCheckInput,
    ModelServiceConfigInput,
)
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.manager.data.deployment.types import MountMetadata, RevisionDraft
from ai.backend.manager.models.runtime_variant import RuntimeVariantRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.deployment.repository import DeploymentRepository
from ai.backend.manager.sokovan.deployment.revision_draft import RevisionDraftReader
from ai.backend.testutils.db import with_tables


@dataclass(frozen=True)
class ResolvedExpectation:
    """Expected attributes on the resolved ``ModelConfig`` at ``models[0]``."""

    name: str
    model_path: str
    service_port: int | None = None
    health_check_path: str | None = None


@pytest.fixture
async def db_with_variant_table(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
    async with with_tables(database_connection, [RuntimeVariantRow]):
        yield database_connection


@pytest.fixture
def reader(
    db_with_variant_table: ExtendedAsyncSAEngine,
) -> RevisionDraftReader:
    # ``load_deployment_revision_read_bundle`` only touches the
    # runtime_variants table when ``preset_id`` is ``None``; the other
    # repository dependencies are not exercised here and can be stubbed.
    repo = DeploymentRepository(
        db=db_with_variant_table,
        storage_manager=MagicMock(),
        valkey_stat=MagicMock(),
        valkey_live=MagicMock(),
        valkey_schedule=MagicMock(),
    )
    return RevisionDraftReader(deployment_repository=repo)


@pytest.fixture
def mounts() -> MountMetadata:
    return MountMetadata(
        model_vfolder_id=VFolderUUID(uuid.uuid4()),
        model_definition_path=None,
        model_mount_destination="/models",
        extra_mounts=[],
    )


async def _seed_variant(
    db: ExtendedAsyncSAEngine,
    baseline: ModelDefinitionDraft,
) -> RuntimeVariantID:
    variant_id = RuntimeVariantID(uuid.uuid4())
    async with db.begin_session() as sess:
        sess.add(
            RuntimeVariantRow(
                id=variant_id,
                name=f"test-variant-{variant_id.hex[:8]}",
                description="BA-5983 merge-test variant baseline",
                reads_vfolder_config_files=False,
                default_model_definition=baseline,
            )
        )
        await sess.commit()
    return variant_id


async def _merge_via_reader(
    reader: RevisionDraftReader,
    variant_id: RuntimeVariantID,
    request: RevisionDraft,
    mounts: MountMetadata,
) -> RevisionDraft:
    drafts = await reader.read_for_deployment_revision(
        runtime_variant_id=variant_id,
        request_draft=request,
        mounts=mounts,
        preset_id=None,
    )
    return functools.reduce(RevisionDraft.merge, drafts, RevisionDraft())


def _assert_resolved_matches(merged: RevisionDraft, expected: ResolvedExpectation) -> None:
    assert merged.model_definition is not None
    resolved = merged.model_definition.to_resolved()
    model = resolved.models[0]
    assert model.name == expected.name
    assert model.model_path == expected.model_path
    if expected.service_port is not None:
        assert model.service is not None
        assert model.service.port == expected.service_port
    if expected.health_check_path is not None:
        assert model.service is not None
        assert model.service.health_check is not None
        assert model.service.health_check.path == expected.health_check_path


class TestMergeWithCompleteBaseline:
    """The variant ships a fully-populated ``default_model_definition``.

    Any request — including all-empty — resolves successfully because
    the DB-side baseline already covers every required field.
    """

    @pytest.fixture
    async def variant_id(
        self,
        db_with_variant_table: ExtendedAsyncSAEngine,
    ) -> RuntimeVariantID:
        return await _seed_variant(
            db_with_variant_table,
            ModelDefinitionDraft(
                models=[
                    ModelConfigDraft(
                        name="baseline-llama",
                        model_path="/models/baseline",
                        service=ModelServiceConfigDraft(
                            port=9000,
                            health_check=ModelHealthCheckDraft(path="/healthz"),
                        ),
                    ),
                ],
            ),
        )

    @pytest.mark.parametrize(
        ("request_input", "expected"),
        [
            pytest.param(
                ModelDefinitionInput(),
                ResolvedExpectation(
                    name="baseline-llama",
                    model_path="/models/baseline",
                    service_port=9000,
                    health_check_path="/healthz",
                ),
                id="empty_request_inherits_baseline",
            ),
            pytest.param(
                ModelDefinitionInput(models=[ModelConfigInput(name="user-name")]),
                ResolvedExpectation(
                    name="user-name",
                    model_path="/models/baseline",
                    service_port=9000,
                    health_check_path="/healthz",
                ),
                id="request_overrides_name_only",
            ),
        ],
    )
    async def test_resolves_to_expected_values(
        self,
        reader: RevisionDraftReader,
        mounts: MountMetadata,
        variant_id: RuntimeVariantID,
        request_input: ModelDefinitionInput,
        expected: ResolvedExpectation,
    ) -> None:
        request = RevisionDraft(model_definition=request_input.to_draft())

        merged = await _merge_via_reader(reader, variant_id, request, mounts)

        _assert_resolved_matches(merged, expected)


class TestMergeWhenBaselineLacksName:
    """The variant baseline omits ``name``. The merge succeeds only
    when the request supplies one — otherwise ``to_resolved()`` raises.
    """

    @pytest.fixture
    async def variant_id(
        self,
        db_with_variant_table: ExtendedAsyncSAEngine,
    ) -> RuntimeVariantID:
        return await _seed_variant(
            db_with_variant_table,
            ModelDefinitionDraft(
                models=[ModelConfigDraft(model_path="/baseline/path")],
            ),
        )

    @pytest.mark.parametrize(
        ("request_input", "expected"),
        [
            pytest.param(
                ModelDefinitionInput(models=[ModelConfigInput(name="from-request")]),
                ResolvedExpectation(name="from-request", model_path="/baseline/path"),
                id="request_supplies_missing_name",
            ),
        ],
    )
    async def test_request_supplying_name_resolves(
        self,
        reader: RevisionDraftReader,
        mounts: MountMetadata,
        variant_id: RuntimeVariantID,
        request_input: ModelDefinitionInput,
        expected: ResolvedExpectation,
    ) -> None:
        request = RevisionDraft(model_definition=request_input.to_draft())

        merged = await _merge_via_reader(reader, variant_id, request, mounts)

        _assert_resolved_matches(merged, expected)

    async def test_empty_request_raises_name_required(
        self,
        reader: RevisionDraftReader,
        mounts: MountMetadata,
        variant_id: RuntimeVariantID,
    ) -> None:
        request = RevisionDraft(model_definition=ModelDefinitionInput().to_draft())

        merged = await _merge_via_reader(reader, variant_id, request, mounts)

        assert merged.model_definition is not None
        with pytest.raises(ValueError, match=r"ModelConfig\.name is required"):
            merged.model_definition.to_resolved()


class TestMergeWhenBaselineLacksServicePort:
    """The variant baseline supplies a ``service`` block without
    ``port``. The merge succeeds only when the request supplies the
    port — otherwise ``to_resolved()`` raises.
    """

    @pytest.fixture
    async def variant_id(
        self,
        db_with_variant_table: ExtendedAsyncSAEngine,
    ) -> RuntimeVariantID:
        return await _seed_variant(
            db_with_variant_table,
            ModelDefinitionDraft(
                models=[
                    ModelConfigDraft(
                        name="baseline",
                        model_path="/baseline/path",
                        service=ModelServiceConfigDraft(
                            health_check=ModelHealthCheckDraft(path="/healthz"),
                        ),
                    ),
                ],
            ),
        )

    @pytest.mark.parametrize(
        ("request_input", "expected"),
        [
            pytest.param(
                ModelDefinitionInput(
                    models=[
                        ModelConfigInput(
                            service=ModelServiceConfigInput(port=8080),
                        ),
                    ],
                ),
                ResolvedExpectation(
                    name="baseline",
                    model_path="/baseline/path",
                    service_port=8080,
                    health_check_path="/healthz",
                ),
                id="request_supplies_service_port",
            ),
        ],
    )
    async def test_request_supplying_port_resolves(
        self,
        reader: RevisionDraftReader,
        mounts: MountMetadata,
        variant_id: RuntimeVariantID,
        request_input: ModelDefinitionInput,
        expected: ResolvedExpectation,
    ) -> None:
        request = RevisionDraft(model_definition=request_input.to_draft())

        merged = await _merge_via_reader(reader, variant_id, request, mounts)

        _assert_resolved_matches(merged, expected)

    async def test_empty_request_raises_port_required(
        self,
        reader: RevisionDraftReader,
        mounts: MountMetadata,
        variant_id: RuntimeVariantID,
    ) -> None:
        request = RevisionDraft(model_definition=ModelDefinitionInput().to_draft())

        merged = await _merge_via_reader(reader, variant_id, request, mounts)

        assert merged.model_definition is not None
        with pytest.raises(ValueError, match=r"ModelServiceConfig\.port is required"):
            merged.model_definition.to_resolved()


class TestMergeWhenBaselineLacksHealthCheckPath:
    """The variant baseline supplies ``service.health_check`` without
    ``path``. The merge succeeds only when the request supplies the
    path — otherwise ``to_resolved()`` raises.
    """

    @pytest.fixture
    async def variant_id(
        self,
        db_with_variant_table: ExtendedAsyncSAEngine,
    ) -> RuntimeVariantID:
        return await _seed_variant(
            db_with_variant_table,
            ModelDefinitionDraft(
                models=[
                    ModelConfigDraft(
                        name="baseline",
                        model_path="/baseline/path",
                        service=ModelServiceConfigDraft(
                            port=8080,
                            health_check=ModelHealthCheckDraft(),
                        ),
                    ),
                ],
            ),
        )

    @pytest.mark.parametrize(
        ("request_input", "expected"),
        [
            pytest.param(
                ModelDefinitionInput(
                    models=[
                        ModelConfigInput(
                            service=ModelServiceConfigInput(
                                health_check=ModelHealthCheckInput(path="/ready"),
                            ),
                        ),
                    ],
                ),
                ResolvedExpectation(
                    name="baseline",
                    model_path="/baseline/path",
                    service_port=8080,
                    health_check_path="/ready",
                ),
                id="request_supplies_health_check_path",
            ),
        ],
    )
    async def test_request_supplying_path_resolves(
        self,
        reader: RevisionDraftReader,
        mounts: MountMetadata,
        variant_id: RuntimeVariantID,
        request_input: ModelDefinitionInput,
        expected: ResolvedExpectation,
    ) -> None:
        request = RevisionDraft(model_definition=request_input.to_draft())

        merged = await _merge_via_reader(reader, variant_id, request, mounts)

        _assert_resolved_matches(merged, expected)

    async def test_empty_request_raises_health_check_path_required(
        self,
        reader: RevisionDraftReader,
        mounts: MountMetadata,
        variant_id: RuntimeVariantID,
    ) -> None:
        request = RevisionDraft(model_definition=ModelDefinitionInput().to_draft())

        merged = await _merge_via_reader(reader, variant_id, request, mounts)

        assert merged.model_definition is not None
        with pytest.raises(ValueError, match=r"ModelHealthCheck\.path is required"):
            merged.model_definition.to_resolved()
