from collections.abc import Callable

type Lint = Callable[[str, str], list[tuple[int, str]]]

ACTION_FILE = "src/ai/backend/manager/services/agent/actions/get.py"


class TestActionFrozenRule:
    def test_action_without_frozen_fails(self, lint: Lint) -> None:
        source = """
            from dataclasses import dataclass

            @dataclass
            class GetAgentAction:
                agent_id: str

            @dataclass(frozen=True)
            class GetAgentActionResult:
                agent_id: str
        """
        assert lint(ACTION_FILE, source) == [(5, "BAI102")]

    def test_action_result_without_frozen_fails(self, lint: Lint) -> None:
        source = """
            from dataclasses import dataclass

            @dataclass(frozen=True)
            class GetAgentAction:
                agent_id: str

            @dataclass
            class GetAgentActionResult:
                agent_id: str
        """
        assert lint(ACTION_FILE, source) == [(9, "BAI102")]

    def test_result_named_by_framework_base_fails(self, lint: Lint) -> None:
        source = """
            from dataclasses import dataclass

            from ai.backend.manager.actions.v2.scope.result import BaseScopeActionResult

            @dataclass
            class EntityShareAnswerResult(BaseScopeActionResult):
                share_id: str
        """
        assert lint(ACTION_FILE, source) == [(7, "BAI102")]

    def test_action_through_local_base_fails(self, lint: Lint) -> None:
        source = """
            from dataclasses import dataclass

            from ai.backend.manager.actions.v2.ops.base import OpsBackendAction

            class _FileActionBase(OpsBackendAction):
                pass

            @dataclass
            class UploadFile(_FileActionBase):
                path: str
        """
        frozen_violations = [v for v in lint(ACTION_FILE, source) if v[1] == "BAI102"]
        assert frozen_violations == [(10, "BAI102")]

    def test_frozen_pair_passes(self, lint: Lint) -> None:
        source = """
            from dataclasses import dataclass

            @dataclass(frozen=True)
            class GetAgentAction:
                agent_id: str

            @dataclass(frozen=True)
            class GetAgentActionResult:
                agent_id: str
        """
        assert lint(ACTION_FILE, source) == []

    def test_other_dataclass_without_frozen_passes(self, lint: Lint) -> None:
        source = """
            from dataclasses import dataclass

            @dataclass
            class AgentServiceArgs:
                agent_id: str
        """
        assert lint("src/ai/backend/manager/services/agent/types.py", source) == []

    def test_class_with_other_framework_base_passes(self, lint: Lint) -> None:
        source = """
            from dataclasses import dataclass

            from ai.backend.manager.actions.v2.lookup.base import LookupKey

            @dataclass
            class AgentNameKey(LookupKey):
                name: str
        """
        assert lint(ACTION_FILE, source) == []

    def test_action_outside_services_passes(self, lint: Lint) -> None:
        source = """
            from dataclasses import dataclass

            @dataclass
            class GetAgentAction:
                agent_id: str
        """
        assert lint("src/ai/backend/manager/api/agent/handler.py", source) == []
