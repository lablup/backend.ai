import pytest

from ai.backend.manager.clients.prometheus.metric_types import ensure_container_metric_name
from ai.backend.manager.errors.metric import InvalidContainerMetricName


class TestEnsureContainerMetricName:
    @pytest.mark.parametrize(
        "metric_name",
        ["cpu_util", "mem", "cuda_mem", "io_scratch_size", "CPU_Util", "atom-max_mem", "vllm:x"],
    )
    def test_accepts_letters_digits_underscores_colons_and_hyphens(self, metric_name: str) -> None:
        ensure_container_metric_name(metric_name)

    @pytest.mark.parametrize(
        "metric_name",
        [
            "",
            'cpu_util"} or vector(1) #',
            "cpu_util\\",
            "cpu_util\nmem",
            "cpu_util|mem",
            "cpu util",
        ],
        ids=["empty", "closing_quote", "backslash", "newline", "regex_union", "space"],
    )
    def test_rejects_any_other_character(self, metric_name: str) -> None:
        with pytest.raises(InvalidContainerMetricName):
            ensure_container_metric_name(metric_name)
