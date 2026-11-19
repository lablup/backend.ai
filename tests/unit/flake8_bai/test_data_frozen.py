from tests.unit.flake8_bai.conftest import Lint

DATA_TYPES = "src/ai/backend/manager/data/agent/types.py"


class TestDataFrozenRule:
    def test_dataclass_without_frozen_fails(self, lint: Lint) -> None:
        source = """
            from dataclasses import dataclass

            @dataclass
            class AgentData:
                id: str
        """
        assert lint(DATA_TYPES, source) == [(5, "BAI101")]

    def test_frozen_false_fails(self, lint: Lint) -> None:
        source = """
            import dataclasses

            @dataclasses.dataclass(frozen=False, slots=True)
            class AgentData:
                id: str
        """
        assert lint(DATA_TYPES, source) == [(5, "BAI101")]

    def test_frozen_dataclass_passes(self, lint: Lint) -> None:
        source = """
            from dataclasses import dataclass

            @dataclass(frozen=True)
            class AgentData:
                id: str
        """
        assert lint(DATA_TYPES, source) == []

    def test_class_without_dataclass_passes(self, lint: Lint) -> None:
        source = """
            import enum

            class AgentStatus(enum.StrEnum):
                ALIVE = "ALIVE"
        """
        assert lint(DATA_TYPES, source) == []

    def test_dataclass_outside_data_passes(self, lint: Lint) -> None:
        source = """
            from dataclasses import dataclass

            @dataclass
            class AgentRow:
                id: str
        """
        assert lint("src/ai/backend/manager/models/agent/row.py", source) == []
