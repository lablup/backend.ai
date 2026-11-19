import ast
from collections.abc import Callable

import pytest

from flake8_bai.baseline import Baseline
from flake8_bai.plugin import Plugin

type Lint = Callable[[str, str], list[tuple[int, str]]]

ACTION_FILE = "src/ai/backend/manager/services/agent/actions/get.py"

UNFROZEN_PAIRS = """
from dataclasses import dataclass

@dataclass
class GetAgentAction:
    agent_id: str

@dataclass
class ListAgentsAction:
    limit: int
"""


@pytest.fixture
def baselined_frozen(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Plugin, "baseline", Baseline({ACTION_FILE: frozenset({"BAI102"})}))


class TestBaseline:
    @pytest.mark.usefixtures("baselined_frozen")
    def test_baselined_code_in_baselined_file_passes(self, lint: Lint) -> None:
        assert lint(ACTION_FILE, UNFROZEN_PAIRS) == [(9, "BAI103")]

    @pytest.mark.usefixtures("baselined_frozen")
    def test_other_file_fails(self, lint: Lint) -> None:
        filename = "src/ai/backend/manager/services/agent/actions/list.py"
        assert lint(filename, UNFROZEN_PAIRS) == [(5, "BAI102"), (9, "BAI102"), (9, "BAI103")]

    @pytest.mark.usefixtures("baselined_frozen")
    def test_relative_prefix_matches(self) -> None:
        tree = ast.parse(UNFROZEN_PAIRS)
        codes = [message.split()[0] for _, _, message, _ in Plugin(tree, f"./{ACTION_FILE}").run()]
        assert codes == ["BAI103"]

    def test_baseline_resource_loads(self) -> None:
        baseline = Baseline.load("baseline.txt")
        assert baseline.allows("src/ai/backend/manager/data/agent/types.py", "BAI101")
