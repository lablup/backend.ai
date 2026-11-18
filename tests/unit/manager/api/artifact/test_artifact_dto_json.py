"""The artifact REST and reservoir DTOs in ``common`` produce the JSON of the former manager DTOs.

``_EXPECTED`` was recorded from the former ``ai.backend.manager.dto`` models with the same inputs.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.data.storage.registries.types import ModelSortKey
from ai.backend.common.dto.manager.artifact.response import (
    ArtifactDTO as UpdatedArtifactDTO,
)
from ai.backend.common.dto.manager.artifact.response import (
    ArtifactRevisionDTO,
    ArtifactRevisionImportTaskDTO,
    CleanupRevisionsResponse,
    GetRevisionReadmeResponse,
    ImportArtifactsResponse,
    UpdateArtifactResponse,
)
from ai.backend.common.dto.manager.artifact_registry.request import (
    ArtifactFilterInput,
    ArtifactOrderingInput,
    DelegateeTargetInput,
    DelegateImportArtifactsRequest,
    DelegateScanArtifactsRequest,
    ImportArtifactsOptionsInput,
    OffsetPaginationInput,
    PaginationInput,
    SearchArtifactsRequest,
)
from ai.backend.common.dto.manager.artifact_registry.response import (
    ArtifactDTO,
    ArtifactRevisionReadmeDTO,
    ArtifactWithRevisionsDTO,
    DelegateScanArtifactsResponse,
    RetrieveArtifactModelResponse,
    SearchArtifactsResponse,
)
from ai.backend.common.dto.manager.artifact_registry.response import (
    ArtifactRevisionDataDTO as RevisionWithReadmeDTO,
)
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.artifact.types import (
    ArtifactAvailability,
    ArtifactOrderField,
    ArtifactRemoteStatus,
    ArtifactStatus,
    ArtifactType,
)


def _id(n: int) -> uuid.UUID:
    return uuid.UUID(int=n)


_TS = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)

_EXPECTED: dict[str, Any] = {
    "cleanup_resp": {
        "artifact_revisions": [
            {
                "artifact_id": "00000000-0000-0000-0000-000000000006",
                "created_at": "2026-01-02T03:04:05Z",
                "digest": "d",
                "id": "00000000-0000-0000-0000-000000000005",
                "remote_status": "SCANNED",
                "size": 3,
                "status": "SCANNED",
                "updated_at": "2026-01-02T03:04:05Z",
                "verification_result": None,
                "version": "v1",
            }
        ]
    },
    "delegate_import_req": {
        "artifact_revision_ids": ["00000000-0000-0000-0000-000000000004"],
        "artifact_type": "MODEL",
        "delegatee_target": None,
        "delegator_reservoir_id": None,
        "options": {"force": True},
    },
    "delegate_scan_req": {
        "artifact_type": "MODEL",
        "delegatee_target": {
            "delegatee_reservoir_id": "00000000-0000-0000-0000-000000000002",
            "target_registry_id": "00000000-0000-0000-0000-000000000003",
        },
        "delegator_reservoir_id": "00000000-0000-0000-0000-000000000001",
        "limit": 10,
        "order": "downloads",
        "search": "q",
    },
    "delegate_scan_resp": {
        "artifacts": [
            {
                "availability": "ALIVE",
                "description": None,
                "extra": {"a": 1},
                "id": "00000000-0000-0000-0000-000000000006",
                "name": "n",
                "readonly": False,
                "registry_id": "00000000-0000-0000-0000-000000000007",
                "registry_type": "huggingface",
                "revisions": [
                    {
                        "artifact_id": "00000000-0000-0000-0000-000000000006",
                        "created_at": "2026-01-02T03:04:05Z",
                        "digest": "d",
                        "id": "00000000-0000-0000-0000-000000000005",
                        "remote_status": "SCANNED",
                        "size": 3,
                        "status": "SCANNED",
                        "updated_at": "2026-01-02T03:04:05Z",
                        "verification_result": None,
                        "version": "v1",
                    }
                ],
                "scanned_at": "2026-01-02T03:04:05Z",
                "source_registry_id": "00000000-0000-0000-0000-000000000008",
                "source_registry_type": "huggingface",
                "type": "MODEL",
                "updated_at": "2026-01-02T03:04:05Z",
            }
        ],
        "readme_data": {"00000000-0000-0000-0000-000000000005": {"readme": "R"}},
        "source_registry_id": "00000000-0000-0000-0000-000000000008",
        "source_registry_type": "reservoir",
    },
    "import_resp": {
        "tasks": [
            {
                "artifact_revision": {
                    "artifact_id": "00000000-0000-0000-0000-000000000006",
                    "created_at": "2026-01-02T03:04:05Z",
                    "digest": "d",
                    "id": "00000000-0000-0000-0000-000000000005",
                    "remote_status": "SCANNED",
                    "size": 3,
                    "status": "SCANNED",
                    "updated_at": "2026-01-02T03:04:05Z",
                    "verification_result": None,
                    "version": "v1",
                },
                "task_id": None,
            }
        ]
    },
    "model_resp": {
        "artifact": {
            "availability": "ALIVE",
            "description": None,
            "extra": {"a": 1},
            "id": "00000000-0000-0000-0000-000000000006",
            "name": "n",
            "readonly": False,
            "registry_id": "00000000-0000-0000-0000-000000000007",
            "registry_type": "huggingface",
            "revisions": [
                {
                    "artifact_id": "00000000-0000-0000-0000-000000000006",
                    "created_at": "2026-01-02T03:04:05Z",
                    "digest": "d",
                    "id": "00000000-0000-0000-0000-000000000005",
                    "readme": "R",
                    "remote_status": "SCANNED",
                    "size": 3,
                    "status": "SCANNED",
                    "updated_at": "2026-01-02T03:04:05Z",
                    "verification_result": None,
                    "version": "v1",
                }
            ],
            "scanned_at": "2026-01-02T03:04:05Z",
            "source_registry_id": "00000000-0000-0000-0000-000000000008",
            "source_registry_type": "huggingface",
            "type": "MODEL",
            "updated_at": "2026-01-02T03:04:05Z",
        }
    },
    "readme_resp": {"readme": "R"},
    "search_req": {
        "filters": {
            "AND": None,
            "NOT": None,
            "OR": None,
            "artifact_type": ["MODEL"],
            "availability": ["ALIVE"],
            "name_filter": {
                "contains": "x",
                "ends_with": None,
                "equals": None,
                "i_contains": None,
                "i_ends_with": None,
                "i_equals": None,
                "i_not_equals": None,
                "i_starts_with": None,
                "not_equals": None,
                "starts_with": None,
            },
            "registry_filter": None,
            "registry_id": None,
            "registry_type": "reservoir",
            "source_filter": None,
            "source_registry_id": None,
            "source_registry_type": None,
        },
        "ordering": {"order_by": [["NAME", True]]},
        "pagination": {"backward": None, "forward": None, "offset": {"limit": 20, "offset": 0}},
    },
    "search_resp": {
        "artifacts": [
            {
                "availability": "ALIVE",
                "description": None,
                "extra": {"a": 1},
                "id": "00000000-0000-0000-0000-000000000006",
                "name": "n",
                "readonly": False,
                "registry_id": "00000000-0000-0000-0000-000000000007",
                "registry_type": "huggingface",
                "revisions": [
                    {
                        "artifact_id": "00000000-0000-0000-0000-000000000006",
                        "created_at": "2026-01-02T03:04:05Z",
                        "digest": "d",
                        "id": "00000000-0000-0000-0000-000000000005",
                        "remote_status": "SCANNED",
                        "size": 3,
                        "status": "SCANNED",
                        "updated_at": "2026-01-02T03:04:05Z",
                        "verification_result": None,
                        "version": "v1",
                    }
                ],
                "scanned_at": "2026-01-02T03:04:05Z",
                "source_registry_id": "00000000-0000-0000-0000-000000000008",
                "source_registry_type": "huggingface",
                "type": "MODEL",
                "updated_at": "2026-01-02T03:04:05Z",
            }
        ]
    },
    "update_resp": {
        "artifact": {
            "availability": "ALIVE",
            "description": None,
            "extra": {"a": 1},
            "id": "00000000-0000-0000-0000-000000000006",
            "name": "n",
            "readonly": False,
            "registry_id": "00000000-0000-0000-0000-000000000007",
            "registry_type": "huggingface",
            "scanned_at": "2026-01-02T03:04:05Z",
            "source_registry_id": "00000000-0000-0000-0000-000000000008",
            "source_registry_type": "huggingface",
            "type": "MODEL",
            "updated_at": "2026-01-02T03:04:05Z",
        }
    },
}


def _revision() -> ArtifactRevisionDTO:
    return ArtifactRevisionDTO(
        id=_id(5),
        artifact_id=_id(6),
        version="v1",
        size=3,
        status=ArtifactStatus.SCANNED,
        remote_status=ArtifactRemoteStatus.SCANNED,
        created_at=_TS,
        updated_at=_TS,
        digest="d",
    )


def _artifact_fields() -> dict[str, Any]:
    return {
        "id": _id(6),
        "name": "n",
        "type": ArtifactType.MODEL,
        "registry_id": _id(7),
        "source_registry_id": _id(8),
        "registry_type": ArtifactRegistryType.HUGGINGFACE,
        "source_registry_type": ArtifactRegistryType.HUGGINGFACE,
        "availability": ArtifactAvailability.ALIVE,
        "scanned_at": _TS,
        "updated_at": _TS,
        "readonly": False,
        "extra": {"a": 1},
    }


def _drop_null_leaves(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _drop_null_leaves(v) for k, v in value.items() if v is not None}
    return value


def test_delegate_scan_request_json() -> None:
    req = DelegateScanArtifactsRequest(
        delegator_reservoir_id=_id(1),
        delegatee_target=DelegateeTargetInput(
            delegatee_reservoir_id=_id(2), target_registry_id=_id(3)
        ),
        artifact_type=ArtifactType.MODEL,
        limit=10,
        order=ModelSortKey.DOWNLOADS,
        search="q",
    )
    assert req.model_dump(mode="json") == _EXPECTED["delegate_scan_req"]


def test_delegate_import_request_json() -> None:
    req = DelegateImportArtifactsRequest(
        artifact_revision_ids=[_id(4)],
        artifact_type=ArtifactType.MODEL,
        options=ImportArtifactsOptionsInput(force=True),
    )
    assert req.model_dump(mode="json") == _EXPECTED["delegate_import_req"]


def test_search_request_json() -> None:
    req = SearchArtifactsRequest(
        pagination=PaginationInput(offset=OffsetPaginationInput(offset=0, limit=20)),
        filters=ArtifactFilterInput(
            name_filter=StringFilter(contains="x"),
            artifact_type=[ArtifactType.MODEL],
            availability=[ArtifactAvailability.ALIVE],
            registry_type=ArtifactRegistryType.RESERVOIR,
        ),
        ordering=ArtifactOrderingInput(order_by=[(ArtifactOrderField.NAME, True)]),
    )
    actual = req.model_dump(mode="json")
    expected = _EXPECTED["search_req"]
    # The shared ``StringFilter`` serialises more keys than the former dataclass; all of them are null.
    assert _drop_null_leaves(actual["filters"]["name_filter"]) == _drop_null_leaves(
        expected["filters"]["name_filter"]
    )
    actual["filters"]["name_filter"] = expected["filters"]["name_filter"] = None
    assert actual == expected


def test_search_response_json() -> None:
    resp = SearchArtifactsResponse(
        artifacts=[ArtifactDTO(**_artifact_fields(), revisions=[_revision()])]
    )
    assert resp.model_dump(mode="json") == _EXPECTED["search_resp"]


def test_delegate_scan_response_json() -> None:
    resp = DelegateScanArtifactsResponse(
        artifacts=[ArtifactDTO(**_artifact_fields(), revisions=[_revision()])],
        source_registry_id=_id(8),
        source_registry_type=ArtifactRegistryType.RESERVOIR,
        readme_data={_id(5): ArtifactRevisionReadmeDTO(readme="R")},
    )
    assert resp.model_dump(mode="json") == _EXPECTED["delegate_scan_resp"]


def test_model_response_json_keeps_readme() -> None:
    revision = RevisionWithReadmeDTO(**_revision().model_dump(), readme="R")
    resp = RetrieveArtifactModelResponse(
        artifact=ArtifactWithRevisionsDTO(**_artifact_fields(), revisions=[revision])
    )
    assert resp.model_dump(mode="json") == _EXPECTED["model_resp"]


def test_cleanup_response_json() -> None:
    resp = CleanupRevisionsResponse(artifact_revisions=[_revision()])
    assert resp.model_dump(mode="json") == _EXPECTED["cleanup_resp"]


def test_import_response_json() -> None:
    resp = ImportArtifactsResponse(
        tasks=[ArtifactRevisionImportTaskDTO(task_id=None, artifact_revision=_revision())]
    )
    assert resp.model_dump(mode="json") == _EXPECTED["import_resp"]


def test_update_response_json() -> None:
    resp = UpdateArtifactResponse(artifact=UpdatedArtifactDTO(**_artifact_fields()))
    assert resp.model_dump(mode="json") == _EXPECTED["update_resp"]


def test_readme_response_json() -> None:
    assert GetRevisionReadmeResponse(readme="R").model_dump(mode="json") == _EXPECTED["readme_resp"]
