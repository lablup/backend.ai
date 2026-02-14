from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ai.backend.manager.dependencies.agents.revision_generator_registry import (
    RevisionGeneratorRegistryDependency,
    RevisionGeneratorRegistryInput,
)


class TestRevisionGeneratorRegistryDependency:
    """Test RevisionGeneratorRegistryDependency lifecycle."""

    @pytest.mark.asyncio
    @patch(
        "ai.backend.manager.dependencies.agents.revision_generator_registry.RevisionGeneratorRegistry",
    )
    async def test_provide_revision_generator_registry(
        self,
        mock_registry_class: MagicMock,
    ) -> None:
        """Dependency should create revision generator registry with correct args."""
        mock_registry = MagicMock()
        mock_registry_class.return_value = mock_registry

        setup_input = RevisionGeneratorRegistryInput(
            deployment_repository=MagicMock(),
        )

        dependency = RevisionGeneratorRegistryDependency()
        async with dependency.provide(setup_input) as registry:
            assert registry is mock_registry
            mock_registry_class.assert_called_once()
