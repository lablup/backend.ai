"""Tests for artifact GraphQL input types."""

from __future__ import annotations

from strawberry import ID

from ai.backend.manager.api.gql.artifact.types import ImportArtifactsInput


def test_import_artifacts_input_options_defaults_to_none() -> None:
    """Test that options defaults to None and resolver pattern works.

    This verifies the fix for TypeError when default_factory was used
    with nested @strawberry.input types.
    See: https://github.com/strawberry-graphql/strawberry/issues/1483
    """
    input_data = ImportArtifactsInput(artifact_revision_ids=[ID("test-id")])
    assert input_data.options is None
