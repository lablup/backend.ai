"""Unit tests for ``RevisionDraftReader``."""

from __future__ import annotations

import functools
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from ai.backend.common.config import (
    DEFAULT_SHELL,
    ModelConfigDraft,
    ModelDefinitionDraft,
    ModelServiceConfigDraft,
)
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.manager.data.deployment.types import (
    DeploymentRevisionReadBundle,
    FetchedModelDefinition,
    MountMetadata,
    RevisionDraft,
)
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.sokovan.deployment.revision_draft.reader import RevisionDraftReader


def _reader() -> RevisionDraftReader:
    return RevisionDraftReader(deployment_repository=cast(Any, object()))


def _mounts(model_mount_destination: str = "/models") -> MountMetadata:
    return MountMetadata(
        model_vfolder_id=VFolderUUID(uuid4()),
        model_definition_path=None,
        model_mount_destination=model_mount_destination,
        extra_mounts=[],
        model_mount_perm=None,
    )


def _variant(
    reads_vfolder_config_files: bool = False,
    default_model_definition: ModelDefinitionDraft | None = None,
) -> RuntimeVariantData:
    return RuntimeVariantData(
        id=RuntimeVariantID(uuid4()),
        name="custom",
        description=None,
        reads_vfolder_config_files=reads_vfolder_config_files,
        default_model_definition=default_model_definition or ModelDefinitionDraft(),
        created_at=datetime(2026, 5, 15, tzinfo=UTC),
        updated_at=None,
    )


def _merge_all(*drafts: RevisionDraft) -> RevisionDraft:
    return functools.reduce(RevisionDraft.merge, drafts, RevisionDraft())


class TestRevisionDraftReaderModelPathDefault:
    def test_adds_lowest_priority_model_path_default(self) -> None:
        drafts = [
            _reader()._model_mount_path_default_draft(_mounts("/mnt/models")),
            RevisionDraft(
                model_definition=ModelDefinitionDraft(models=[ModelConfigDraft(name="base")])
            ),
            RevisionDraft(
                model_definition=ModelDefinitionDraft(
                    models=[
                        ModelConfigDraft(name="override-0"),
                    ]
                )
            ),
        ]

        merged = _merge_all(*drafts)

        assert merged.model_definition is not None
        assert merged.model_definition.models is not None
        assert merged.model_definition.models[0].name == "override-0"
        assert merged.model_definition.models[0].model_path == "/mnt/models"


def _repository(
    variant: RuntimeVariantData,
    model_definition_yaml: Mapping[str, Any] | None = None,
) -> MagicMock:
    """Mock only the I/O boundary: DB bundle + vfolder file fetches.

    The yaml payload still goes through the real ``from_file_payload`` parse,
    so the test covers the same normalization a stored file would get.
    """
    repository = MagicMock()
    repository.load_deployment_revision_read_bundle = AsyncMock(
        return_value=DeploymentRevisionReadBundle(
            variant=variant, preset=None, preset_resource_slots=None
        )
    )
    repository.fetch_deployment_config = AsyncMock(return_value=None)
    repository.fetch_model_definition = AsyncMock(
        return_value=(
            FetchedModelDefinition(
                path="model-definition.yaml",
                model_definition=ModelDefinitionDraft.from_file_payload(model_definition_yaml),
            )
            if model_definition_yaml is not None
            else None
        )
    )
    return repository


def _model_definition(merged: RevisionDraft) -> ModelDefinitionDraft:
    assert merged.model_definition is not None
    return merged.model_definition


def _service_draft(merged: RevisionDraft) -> ModelServiceConfigDraft:
    models = _model_definition(merged).models
    assert models
    service = models[0].service
    assert service is not None
    return service


@dataclass(frozen=True)
class PrecedenceCase:
    """One layer-precedence scenario; unset payload layers default to absent."""

    expected_start_command: str
    expected_port: int
    # Resolved shell — layers below may leave it unset, then it resolves to DEFAULT_SHELL.
    expected_shell: str
    reads_files: bool
    yaml_payload: Mapping[str, Any] | None = None
    request_payload: Mapping[str, Any] | None = None


class DraftMergeChain:
    """Runs the real revision-draft chain end to end; only the I/O boundary is mocked.

    Layer order (low → high), merged with the same reduce as
    ``deployment_controller.add_revision`` (= ``_merge_all``):

    1. model-mount ``model_path`` default (reader-injected)
    2. variant ``default_model_definition`` (DB bundle — mocked)
    3. model-definition.yaml (file I/O mocked; real ``from_file_payload`` parse)
    4. request draft
    """

    async def merge(
        self,
        *,
        variant_default: Mapping[str, Any],
        reads_files: bool,
        yaml_payload: Mapping[str, Any] | None = None,
        request_payload: Mapping[str, Any] | None = None,
    ) -> RevisionDraft:
        variant = _variant(
            reads_vfolder_config_files=reads_files,
            default_model_definition=ModelDefinitionDraft.model_validate(variant_default),
        )
        reader = RevisionDraftReader(deployment_repository=_repository(variant, yaml_payload))
        request = ModelDefinitionDraft.model_validate(request_payload) if request_payload else None
        drafts = await reader.read_for_deployment_revision(
            runtime_variant_id=variant.id,
            request_draft=RevisionDraft(mounts=_mounts(), model_definition=request),
            preset_id=None,
        )
        return _merge_all(*drafts)


class TestMergeChainModelDefinition:
    """Scenario-level checks over ``DraftMergeChain`` — see its docstring for the wiring."""

    @pytest.fixture
    def chain(self) -> DraftMergeChain:
        return DraftMergeChain()

    @pytest.fixture
    def variant_default(self) -> Mapping[str, Any]:
        """Standard baseline: name/port/start_command + enabled health_check; ``shell`` unset."""
        return {
            "models": [
                {
                    "name": "demo",
                    "service": {
                        "port": 8080,
                        "start_command": "variant-cmd",
                        "health_check": {"enable": True, "path": "/health"},
                    },
                }
            ]
        }

    @pytest.fixture
    def variant_without_health_check(self) -> Mapping[str, Any]:
        """Minimal baseline with no health_check block."""
        return {"models": [{"name": "demo", "service": {"port": 8080}}]}

    @pytest.mark.parametrize(
        "case",
        [
            pytest.param(
                PrecedenceCase(
                    yaml_payload={"models": [{"service": {"start_command": "yaml-cmd"}}]},
                    reads_files=True,
                    expected_start_command="yaml-cmd",
                    expected_port=8080,
                    # No layer sets shell — stays unset through the chain.
                    expected_shell=DEFAULT_SHELL,
                ),
                id="yaml-overrides-variant-default",
            ),
            pytest.param(
                PrecedenceCase(
                    yaml_payload={
                        "models": [
                            {
                                "service": {
                                    "start_command": "yaml-cmd",
                                    "port": 8081,
                                    "shell": "/bin/sh",
                                }
                            }
                        ]
                    },
                    request_payload={
                        "models": [
                            {
                                "service": {
                                    "start_command": "request-cmd",
                                    "port": 9000,
                                    "shell": "/bin/zsh",
                                }
                            }
                        ]
                    },
                    reads_files=True,
                    expected_start_command="request-cmd",
                    expected_port=9000,
                    expected_shell="/bin/zsh",
                ),
                id="request-overrides-yaml-and-variant-default",
            ),
            pytest.param(
                PrecedenceCase(
                    yaml_payload={"models": [{"service": {"start_command": "yaml-cmd"}}]},
                    request_payload={"models": [{"service": {"port": 9000, "shell": "/bin/zsh"}}]},
                    reads_files=True,
                    # Per-field both ways: start_command from yaml, port/shell from request.
                    expected_start_command="yaml-cmd",
                    expected_port=9000,
                    expected_shell="/bin/zsh",
                ),
                id="request-partial-merges-per-field",
            ),
            pytest.param(
                PrecedenceCase(
                    yaml_payload={
                        "models": [{"service": {"start_command": "yaml-cmd", "shell": "/bin/sh"}}]
                    },
                    reads_files=False,
                    expected_start_command="variant-cmd",
                    expected_port=8080,
                    expected_shell=DEFAULT_SHELL,
                ),
                id="yaml-skipped-when-variant-not-reading-files",
            ),
        ],
    )
    async def test_layer_precedence(
        self,
        chain: DraftMergeChain,
        variant_default: Mapping[str, Any],
        case: PrecedenceCase,
    ) -> None:
        merged = await chain.merge(
            variant_default=variant_default,
            reads_files=case.reads_files,
            yaml_payload=case.yaml_payload,
            request_payload=case.request_payload,
        )

        service = _service_draft(merged)
        assert service.start_command == case.expected_start_command
        assert service.port == case.expected_port
        # The variant default's nested health_check survives every combination above.
        assert service.health_check is not None
        assert service.health_check.path == "/health"
        resolved_service = _model_definition(merged).to_resolved().models[0].service
        assert resolved_service is not None
        assert resolved_service.shell == case.expected_shell

    async def test_explicit_null_shell_preserved(
        self, chain: DraftMergeChain, variant_default: Mapping[str, Any]
    ) -> None:
        merged = await chain.merge(
            variant_default=variant_default,
            reads_files=True,
            yaml_payload={"models": [{"service": {"start_command": "yaml-cmd", "shell": None}}]},
        )

        assert "shell" in _service_draft(merged).model_fields_set
        resolved_service = _model_definition(merged).to_resolved().models[0].service
        assert resolved_service is not None
        assert resolved_service.shell is None

    async def test_empty_health_check_opts_out(
        self, chain: DraftMergeChain, variant_default: Mapping[str, Any]
    ) -> None:
        merged = await chain.merge(
            variant_default=variant_default,
            reads_files=True,
            yaml_payload={
                "models": [{"service": {"start_command": "yaml-cmd", "health_check": None}}]
            },
        )

        health_check = _service_draft(merged).health_check
        assert health_check is not None
        assert health_check.enable is False
        assert _model_definition(merged).to_resolved().health_check_config() is None

    async def test_health_check_auto_enables_with_defaults(
        self, chain: DraftMergeChain, variant_without_health_check: Mapping[str, Any]
    ) -> None:
        merged = await chain.merge(
            variant_default=variant_without_health_check,
            reads_files=True,
            yaml_payload={
                "models": [
                    {"service": {"start_command": "yaml-cmd", "health_check": {"path": "/live"}}}
                ]
            },
        )

        health_check = _service_draft(merged).health_check
        assert health_check is not None
        assert health_check.enable is True
        assert health_check.path == "/live"
        assert "interval" not in health_check.model_fields_set
        resolved_health_check = _model_definition(merged).to_resolved().health_check_config()
        assert resolved_health_check is not None
        assert resolved_health_check.interval == 10.0  # strict-type Field default


class TestRevisionDraftReaderVFolderDrafts:
    async def test_records_resolved_default_model_definition_path(self) -> None:
        repository = MagicMock()
        repository.fetch_deployment_config = AsyncMock(return_value=None)
        repository.fetch_model_definition = AsyncMock(
            return_value=FetchedModelDefinition(
                path="model-definition.yml",
                model_definition=ModelDefinitionDraft(models=[ModelConfigDraft(name="from-file")]),
            )
        )
        reader = RevisionDraftReader(deployment_repository=repository)
        variant = _variant(reads_vfolder_config_files=True)

        drafts = await reader._read_vfolder_drafts(_mounts(), variant)
        merged = _merge_all(*drafts)

        assert merged.mounts is not None
        assert merged.mounts.model_definition_path == "model-definition.yml"
        assert merged.model_definition is not None
        assert merged.model_definition.models is not None
        assert merged.model_definition.models[0].name == "from-file"
