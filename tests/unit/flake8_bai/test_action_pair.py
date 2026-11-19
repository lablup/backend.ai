from tests.unit.flake8_bai.conftest import Lint

ACTION_FILE = "src/ai/backend/manager/services/agent/actions/get.py"


class TestActionPairRule:
    def test_two_pairs_in_a_file_fail(self, lint: Lint) -> None:
        source = """
            from dataclasses import dataclass

            @dataclass(frozen=True)
            class GetAgentAction:
                agent_id: str

            @dataclass(frozen=True)
            class GetAgentActionResult:
                agent_id: str

            @dataclass(frozen=True)
            class ListAgentsAction:
                limit: int

            @dataclass(frozen=True)
            class ListAgentsActionResult:
                agent_ids: list[str]
        """
        assert lint(ACTION_FILE, source) == [(13, "BAI103"), (17, "BAI103")]

    def test_second_result_named_by_framework_base_fails(self, lint: Lint) -> None:
        source = """
            from ai.backend.manager.actions.v2.ops.result import EntitiesOpsResult

            class SearchAgentsActionResult(EntitiesOpsResult): ...
            class ListAgentsResult(EntitiesOpsResult): ...
        """
        assert lint(ACTION_FILE, source) == [(5, "BAI103")]

    def test_one_pair_passes(self, lint: Lint) -> None:
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

    def test_two_pairs_outside_services_pass(self, lint: Lint) -> None:
        source = """
            class GetAgentAction: ...
            class GetAgentActionResult: ...
            class ListAgentsAction: ...
            class ListAgentsActionResult: ...
        """
        assert lint("src/ai/backend/manager/actions/action/base.py", source) == []
