"""DB-backed verification of the BA-5983 revision merge contract.

A real ``RuntimeVariantRow`` is seeded via a fixture (so the variant's
``default_model_definition`` round-trips through ``PydanticColumn``
serialization). The production ``RevisionDraftReader`` +
``RevisionDraft.merge`` pipeline is then run against request drafts
built from various ``ModelDefinitionInput`` shapes; the parametrized
table only carries the request input and the expected outcome.

Two scenario groups, each pinned to its own DB baseline fixture:

- ``TestMergeWithFullBaseline`` — variant ships every required field;
  the parametrized inputs probe how different requests combine with
  it (inherit-all, partial override).
- ``TestMergeRaisesWithIncompleteBaseline`` — variant ships an
  incomplete definition where ``to_resolved()`` is expected to raise
  because no source supplies a required nested field. Each parametrize
  entry pairs an incomplete baseline shape with the expected error
  pattern; the request is always all-empty.
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


class TestMergeWithFullBaseline:
    """Baseline supplies every required field. The parametrize table
    pairs each ``ModelDefinitionInput`` shape with the resolved values
    we expect after merging it against this baseline."""

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
                id="empty_request_inherits_full_baseline",
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
    async def test_merge_resolves_to_expected_values(
        self,
        reader: RevisionDraftReader,
        mounts: MountMetadata,
        variant_id: RuntimeVariantID,
        request_input: ModelDefinitionInput,
        expected: ResolvedExpectation,
    ) -> None:
        request = RevisionDraft(model_definition=request_input.to_draft())

        merged = await _merge_via_reader(reader, variant_id, request, mounts)

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


class TestMergeRaisesWithIncompleteBaseline:
    """Each parametrize entry seeds its own incomplete baseline (via the
    ``baseline_factory``) and expects ``to_resolved()`` to raise because
    no source supplies a required field. The request is always
    all-empty so the failure mode comes entirely from the baseline."""

    @pytest.mark.parametrize(
        ("incomplete_baseline", "error_pattern"),
        [
            pytest.param(
                # Reader's mount-destination default also fills model_path,
                # so the only required ``ModelConfig`` field that ends up
                # unfilled is ``name``.
                ModelDefinitionDraft(models=[ModelConfigDraft(model_path="/p")]),
                r"ModelConfig\.name is required",
                id="name_unfilled",
            ),
            pytest.param(
                ModelDefinitionDraft(
                    models=[
                        ModelConfigDraft(
                            name="n",
                            model_path="/p",
                            service=ModelServiceConfigDraft(),
                        ),
                    ],
                ),
                r"ModelServiceConfig\.port is required",
                id="service_port_unfilled",
            ),
            pytest.param(
                ModelDefinitionDraft(
                    models=[
                        ModelConfigDraft(
                            name="n",
                            model_path="/p",
                            service=ModelServiceConfigDraft(
                                port=8080,
                                health_check=ModelHealthCheckDraft(),
                            ),
                        ),
                    ],
                ),
                r"ModelHealthCheck\.path is required",
                id="health_check_path_unfilled",
            ),
        ],
    )
    async def test_required_field_unfilled_after_merge_raises(
        self,
        db_with_variant_table: ExtendedAsyncSAEngine,
        reader: RevisionDraftReader,
        mounts: MountMetadata,
        incomplete_baseline: ModelDefinitionDraft,
        error_pattern: str,
    ) -> None:
        variant_id = await _seed_variant(db_with_variant_table, incomplete_baseline)
        request = RevisionDraft(model_definition=ModelDefinitionInput().to_draft())

        merged = await _merge_via_reader(reader, variant_id, request, mounts)

        assert merged.model_definition is not None
        with pytest.raises(ValueError, match=error_pattern):
            merged.model_definition.to_resolved()
