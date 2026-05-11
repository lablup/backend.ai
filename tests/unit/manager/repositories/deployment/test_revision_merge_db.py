"""DB-backed verification of the BA-5983 revision merge contract.

Inserts real ``RuntimeVariantRow`` records (so the variant's
``default_model_definition`` round-trips through ``PydanticColumn``
serialization) and runs the production ``RevisionDraftReader`` +
``RevisionDraft.merge`` pipeline against a request draft built from
``ModelDefinitionInput.to_draft()``. The resolved output is then
inspected to confirm:

- An empty request inherits every required field from the variant
  baseline; the resolved ``ModelDefinition`` carries the baseline
  values verbatim.
- A request that supplies a subset of fields overrides only those
  fields; baseline-supplied fields survive.
- When no source supplies a required field, ``to_resolved()`` raises
  ``ValueError`` with the field-specific message.

This exercises the full read path (DB → ``PydanticColumn`` →
``RuntimeVariantData`` → ``RevisionDraft``) plus the merge and
resolve phases that the ``add_model_revision`` action ultimately runs.
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


class TestRevisionMergeWithRealVariantBaseline:
    @pytest.fixture
    async def db_with_variant_table(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, [RuntimeVariantRow]):
            yield database_connection

    @pytest.fixture
    def reader(
        self,
        db_with_variant_table: ExtendedAsyncSAEngine,
    ) -> RevisionDraftReader:
        # ``load_deployment_revision_read_bundle`` only touches the
        # runtime_variants table when ``preset_id`` is ``None``; the
        # other repository dependencies are not exercised and can be
        # stubbed out.
        repo = DeploymentRepository(
            db=db_with_variant_table,
            storage_manager=MagicMock(),
            valkey_stat=MagicMock(),
            valkey_live=MagicMock(),
            valkey_schedule=MagicMock(),
        )
        return RevisionDraftReader(deployment_repository=repo)

    @pytest.fixture
    def mounts(self) -> MountMetadata:
        return MountMetadata(
            model_vfolder_id=VFolderUUID(uuid.uuid4()),
            model_definition_path=None,
            model_mount_destination="/models",
            extra_mounts=[],
        )

    @staticmethod
    async def _seed_variant_baseline(
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

    @staticmethod
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

    @pytest.mark.parametrize(
        ("baseline", "request_input", "expected"),
        [
            pytest.param(
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
                ModelDefinitionDraft(
                    models=[
                        ModelConfigDraft(name="baseline-name", model_path="/baseline/path"),
                    ],
                ),
                ModelDefinitionInput(models=[ModelConfigInput(name="user-name")]),
                ResolvedExpectation(name="user-name", model_path="/baseline/path"),
                id="request_overrides_name_baseline_keeps_model_path",
            ),
        ],
    )
    async def test_merge_resolves_to_expected_values(
        self,
        db_with_variant_table: ExtendedAsyncSAEngine,
        reader: RevisionDraftReader,
        mounts: MountMetadata,
        baseline: ModelDefinitionDraft,
        request_input: ModelDefinitionInput,
        expected: ResolvedExpectation,
    ) -> None:
        variant_id = await self._seed_variant_baseline(db_with_variant_table, baseline)
        request = RevisionDraft(model_definition=request_input.to_draft())

        merged = await self._merge_via_reader(reader, variant_id, request, mounts)

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

    @pytest.mark.parametrize(
        ("baseline", "error_pattern"),
        [
            pytest.param(
                # baseline supplies model_path only; reader's mount-destination
                # default would also fill model_path → only ``name`` remains unfilled.
                ModelDefinitionDraft(models=[ModelConfigDraft(model_path="/p")]),
                r"ModelConfig\.name is required",
                id="name_unfilled_across_baseline_and_request",
            ),
            pytest.param(
                # baseline supplies name + model_path + an empty service →
                # service.port has no default and no override.
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
                id="service_port_unfilled_across_baseline_and_request",
            ),
            pytest.param(
                # baseline supplies service.port but an empty health_check →
                # health_check.path has no default.
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
                id="health_check_path_unfilled_across_baseline_and_request",
            ),
        ],
    )
    async def test_required_field_unfilled_after_merge_raises(
        self,
        db_with_variant_table: ExtendedAsyncSAEngine,
        reader: RevisionDraftReader,
        mounts: MountMetadata,
        baseline: ModelDefinitionDraft,
        error_pattern: str,
    ) -> None:
        # Request is always an all-empty ``ModelDefinitionInput`` for these
        # scenarios — the merge result depends entirely on whether the
        # baseline (or reader-supplied defaults) cover every required field.
        variant_id = await self._seed_variant_baseline(db_with_variant_table, baseline)
        request = RevisionDraft(model_definition=ModelDefinitionInput().to_draft())

        merged = await self._merge_via_reader(reader, variant_id, request, mounts)

        assert merged.model_definition is not None
        with pytest.raises(ValueError, match=error_pattern):
            merged.model_definition.to_resolved()
