from __future__ import annotations

from ai.backend.manager.api.gql.base import StringFilter as StringFilterGQL
from ai.backend.manager.api.gql.deployment.types.revision_preset import (
    DeploymentRevisionPresetFilterGQL,
)


class TestDeploymentRevisionPresetFilterCombinators:
    def test_empty(self) -> None:
        dto = DeploymentRevisionPresetFilterGQL().to_pydantic()
        assert dto.AND is None and dto.OR is None and dto.NOT is None

    def test_and(self) -> None:
        f = DeploymentRevisionPresetFilterGQL(
            AND=[
                DeploymentRevisionPresetFilterGQL(name=StringFilterGQL(contains="a")),
                DeploymentRevisionPresetFilterGQL(name=StringFilterGQL(contains="b")),
            ]
        )
        dto = f.to_pydantic()
        assert dto.AND is not None
        assert len(dto.AND) == 2

    def test_or(self) -> None:
        f = DeploymentRevisionPresetFilterGQL(
            OR=[DeploymentRevisionPresetFilterGQL(name=StringFilterGQL(contains="a"))]
        )
        assert f.to_pydantic().OR is not None

    def test_not(self) -> None:
        f = DeploymentRevisionPresetFilterGQL(
            NOT=[DeploymentRevisionPresetFilterGQL(name=StringFilterGQL(equals="x"))]
        )
        assert f.to_pydantic().NOT is not None
