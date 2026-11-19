from tests.unit.flake8_bai.conftest import Lint

MANAGER_INIT = "src/ai/backend/manager/services/agent/__init__.py"

IMPORTING_SOURCE = """
    from ai.backend.manager.services.agent.service import AgentService
    import os
"""


class TestInitImportRule:
    def test_import_in_manager_init_fails(self, lint: Lint) -> None:
        assert lint(MANAGER_INIT, IMPORTING_SOURCE) == [(2, "BAI001"), (3, "BAI001")]

    def test_nested_import_in_manager_init_fails(self, lint: Lint) -> None:
        source = """
            def load() -> None:
                import json
        """
        assert lint(MANAGER_INIT, source) == [(3, "BAI001")]

    def test_manager_init_without_import_passes(self, lint: Lint) -> None:
        assert lint(MANAGER_INIT, '"""Agent service."""\n') == []

    def test_manager_module_other_than_init_passes(self, lint: Lint) -> None:
        filename = "src/ai/backend/manager/services/agent/service.py"
        assert lint(filename, IMPORTING_SOURCE) == []

    def test_init_outside_manager_passes(self, lint: Lint) -> None:
        filename = "src/ai/backend/common/dto/__init__.py"
        assert lint(filename, IMPORTING_SOURCE) == []
