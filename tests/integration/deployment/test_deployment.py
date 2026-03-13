from __future__ import annotations

import pytest

from ai.backend.client.v2.registry import BackendAIClientRegistry


@pytest.mark.integration
class TestDeploymentLifecycle:
    """Full lifecycle: create -> get -> update -> search -> destroy.

    Requires a running manager with real infrastructure (agents, images,
    vfolders, scaling groups). Skipped until full test infrastructure is
    available.
    """

    async def test_create_get_update_search_destroy(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        pytest.skip("Requires live agent infrastructure not available in CI")


@pytest.mark.integration
class TestRevisionLifecycle:
    """Revision lifecycle: create deployment -> create revision -> get -> search.

    Requires a running manager with real infrastructure.
    """

    async def test_create_and_search_revisions(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        pytest.skip("Requires live agent infrastructure not available in CI")


@pytest.mark.integration
class TestRouteOperations:
    """Route operations: create deployment -> activate -> search routes -> update traffic.

    Requires a running manager with real infrastructure.
    """

    async def test_search_and_update_routes(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        pytest.skip("Requires live agent infrastructure not available in CI")
