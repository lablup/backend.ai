from __future__ import annotations

import decimal
import json
import textwrap
from collections import defaultdict
from typing import Any, Callable, Mapping, Optional

import humanize

from ai.backend.common.types import MetricValue

from .types import AbstractOutputFormatter, FieldSpec


def format_stats(raw_stats: Optional[str], indent="") -> str:
    if raw_stats is None:
        return "(unavailable)"
    stats = json.loads(raw_stats)
    text = "\n".join(f"- {k + ': ':18s}{v}" for k, v in stats.items())
    return "\n" + textwrap.indent(text, indent)


def format_multiline(value: Any, indent_length: int) -> str:
    buf = []
    for idx, line in enumerate(str(value).strip().splitlines()):
        if idx == 0:
            buf.append(line)
        else:
            buf.append((" " * indent_length) + line)
    return "\n".join(buf)


def format_nested_dicts(value: Mapping[str, Mapping[str, Any]]) -> str:
    """
    Format a mapping from string keys to sub-mappings.
    """
    rows = []
    if not value:
        rows.append("(empty)")
    else:
        for outer_key, outer_value in value.items():
            if isinstance(outer_value, dict):
                if outer_value:
                    rows.append(f"+ {outer_key}")
                    inner_rows = format_nested_dicts(outer_value)
                    rows.append(textwrap.indent(inner_rows, prefix="  "))
                else:
                    rows.append(f"+ {outer_key}: (empty)")
            else:
                if outer_value is None:
                    rows.append(f"- {outer_key}: (null)")
                else:
                    # TODO: refactor as a formatter
                    if outer_key == "shmem":
                        rows.append(
                            f"- {outer_key}:"
                            f" {humanize.naturalsize(str(outer_value), binary=True, gnu=True)}"
                        )
                    else:
                        rows.append(f"- {outer_key}: {outer_value}")
    return "\n".join(rows)


def format_value(value: Any) -> str:
    if value is None:
        return "(null)"
    if isinstance(value, (dict, list, set)) and not value:
        return "(empty)"
    return str(value)


class OutputFormatter(AbstractOutputFormatter):
    """
    The base implementation of output formats.
    """

    def format_console(self, value: Any, field: FieldSpec) -> str:
        if value is None:
            return "(null)"
        if isinstance(value, (dict, list, set)) and not value:
            return "(empty)"
        elif isinstance(value, dict):
            return (
                "{"
                + ", ".join(f"{k}: {self.format_console(v, field)}" for k, v in value.items())
                + "}"
            )
        elif isinstance(value, (list, tuple, set)):
            return "[" + ", ".join(self.format_console(v, field) for v in value) + "]"
        return str(value)

    def format_json(self, value: Any, field: FieldSpec) -> Any:
        if value is None:
            return None
        if isinstance(value, decimal.Decimal):
            return str(value)
        elif isinstance(value, dict):
            return {k: self.format_json(v, field) for k, v in value.items()}
        elif isinstance(value, (list, tuple)):
            return [self.format_json(v, field) for v in value]
        return value


class NestedDictOutputFormatter(OutputFormatter):
    def format_console(self, value: Any, field: FieldSpec) -> str:
        if value is None:
            return "(null)"
        value = json.loads(value)
        return format_nested_dicts(value)

    def format_json(self, value: Any, field: FieldSpec) -> Any:
        if value is None:
            return None
        return json.loads(value)


class MiBytesOutputFormatter(OutputFormatter):
    def format_console(self, value: Any, field: FieldSpec) -> str:
        if value is not None:
            value = round(value / 2**20, 1)
        return super().format_console(value, field)

    def format_json(self, value: Any, field: FieldSpec) -> Any:
        if value is not None:
            value = round(value / 2**20, 1)
        return super().format_json(value, field)


class SizeBytesOutputFormatter(OutputFormatter):
    def format_console(self, value: Any, field: FieldSpec) -> str:
        if value is not None:
            value = humanize.naturalsize(value, binary=True, gnu=True)
        return super().format_console(value, field)

    def format_json(self, value: Any, field: FieldSpec) -> Any:
        if value is not None:
            value = humanize.naturalsize(value, binary=True, gnu=True)
        return super().format_json(value, field)


class SubFieldOutputFormatter(OutputFormatter):
    def __init__(self, subfield_name: str) -> None:
        self._subfield_name = subfield_name

    def format_console(self, value: Any, field: FieldSpec) -> str:
        return super().format_console(value[self._subfield_name], field)

    def format_json(self, value: Any, field: FieldSpec) -> Any:
        return super().format_json(value[self._subfield_name], field)


class CustomizedImageOutputFormatter(OutputFormatter):
    def _get_name(self, labels: Any) -> str:
        customized_name = [
            label["value"] for label in labels if label["key"] == "ai.backend.customized-image.name"
        ]
        assert len(customized_name) == 1
        owner_email = [
            label["value"]
            for label in labels
            if label["key"] == "ai.backend.customized-image.user.email"
        ]
        assert len(owner_email) == 1
        return f"{customized_name[0]} (Owner: {owner_email[0]})"

    def format_console(self, value: Any, field: FieldSpec) -> str:
        return super().format_console(self._get_name(value), field)

    def format_json(self, value: Any, field: FieldSpec) -> Any:
        return super().format_json(self._get_name(value), field)


class ResourceSlotFormatter(OutputFormatter):
    def format_console(self, value: Any, field: FieldSpec) -> str:
        value = json.loads(value)
        if mem := value.get("mem"):
            value["mem"] = humanize.naturalsize(mem, binary=True, gnu=True)

        return ", ".join(f"{k}:{v}" for k, v in value.items())

    def format_json(self, value: Any, field: FieldSpec) -> Any:
        return json.loads(value)


default_output_formatter = OutputFormatter()
nested_dict_formatter = NestedDictOutputFormatter()
mibytes_output_formatter = MiBytesOutputFormatter()
resource_slot_formatter = ResourceSlotFormatter()
sizebytes_output_formatter = SizeBytesOutputFormatter()


class AgentStatFormatter(OutputFormatter):
    def format_console(self, value: Any, field: FieldSpec) -> str:
        try:
            raw_stats = json.loads(value)
        except TypeError:
            return ""

        percent_formatter = lambda metric, _: "{} %".format(metric["pct"])
        value_formatters: Mapping[str, Callable[[MetricValue, bool], str]] = {
            "bytes": lambda metric, binary: "{} / {}".format(
                humanize.naturalsize(int(metric["current"]), binary=binary, gnu=binary),
                (
                    humanize.naturalsize(int(metric["capacity"]), binary=binary, gnu=binary)
                    if metric["capacity"] is not None
                    else "(unknown)"
                ),
            ),
            "Celsius": lambda metric, _: "{:,} C".format(
                float(metric["current"]),
            ),
            "bps": lambda metric, _: "{}/s".format(
                humanize.naturalsize(float(metric["current"])),
            ),
            "pct": percent_formatter,
            "percent": percent_formatter,
            "%": percent_formatter,
        }

        def format_value(metric: MetricValue, binary: bool) -> str:
            unit_hint = metric["unit_hint"]
            formatter = value_formatters.get(
                unit_hint,
                # a fallback implementation
                lambda m, _: "{} / {} {}".format(
                    m["current"],
                    "(unknown)" if m["capacity"] is None else m["capacity"],
                    "" if unit_hint == "count" else unit_hint,
                ),
            )
            return formatter(metric, binary)

        bufs = []
        node_metric_bufs = []
        for stat_key, metric in raw_stats["node"].items():
            if stat_key == "cpu_util":
                num_cores = len(raw_stats["devices"]["cpu_util"])
                if metric["pct"] is None:
                    node_metric_bufs.append(f"{stat_key}: (calculating...) % ({num_cores} cores)")
                else:
                    node_metric_bufs.append(f"{stat_key}: {metric['pct']} % ({num_cores} cores)")
            else:
                binary = stat_key == "mem"
                node_metric_bufs.append(f"{stat_key}: {format_value(metric, binary)}")

        bufs.append(", ".join(node_metric_bufs))
        dev_metric_bufs = []
        for stat_key, per_dev_metric in raw_stats["devices"].items():
            dev_metric_bufs.append(f"+ {stat_key}")
            if stat_key == "cpu_util" and len(per_dev_metric) > 8:
                dev_metric_bufs.append(
                    "  - (per-core stats hidden for large CPUs with more than 8 cores)",
                )
            else:
                binary = stat_key == "mem"
                for dev_id, metric in per_dev_metric.items():
                    dev_metric_bufs.append(
                        f"  - {dev_id}: {format_value(metric, binary)}",
                    )
        bufs.append("\n".join(dev_metric_bufs))
        return "\n".join(bufs)

    def format_json(self, value: Any, field: FieldSpec) -> Any:
        # TODO: improve
        return self.format_console(value, field)


class GroupListFormatter(OutputFormatter):
    def format_console(self, value: Any, field: FieldSpec) -> str:
        return ", ".join(g["name"] for g in value)

    def format_json(self, value: Any, field: FieldSpec) -> Any:
        return value


class InlineRoutingFormatter(OutputFormatter):
    def format_console(self, value: Any, field: FieldSpec) -> str:
        count_by_status: defaultdict[int, int] = defaultdict(int)
        for route in value:
            count_by_status[route["status"]] += 1
        return ", ".join([
            f"{key} {value}" for key, value in sorted(count_by_status.items(), key=lambda kv: kv[0])
        ])

    def format_json(self, value: Any, field: FieldSpec) -> Any:
        return value


class KernelStatFormatter(OutputFormatter):
    def format_console(self, value: Any, field: FieldSpec) -> str:
        return format_stats(value)

    def format_json(self, value: Any, field: FieldSpec) -> Any:
        return value


class NestedObjectFormatter(OutputFormatter):
    def format_json(self, value: Any, field: FieldSpec) -> Any:
        assert isinstance(value, list)
        return [
            {
                f.alt_name: f.formatter.format_json(item[f.field_name], f)
                for f in field.subfields.values()
            }
            for item in value
        ]


def _fit_multiline_in_cell(text: str, indent: str) -> str:
    if "\n" in text:
        return "\n" + textwrap.indent(text, indent)
    else:
        return text


class ContainerListFormatter(NestedObjectFormatter):
    def format_console(self, value: Any, field: FieldSpec, indent="") -> str:
        assert isinstance(value, list)
        if len(value) == 0:
            text = "(no sub-containers belonging to the session)"
        else:
            text = ""
            for item in value:
                text += f"+ {item['id']}\n"
                text += "\n".join(
                    f"  - {f.humanized_name}: "
                    f"{_fit_multiline_in_cell(f.formatter.format_console(item[f.field_name], f), '    ')}"  # noqa
                    for f in field.subfields.values()
                    if f.field_name != "id"
                )
        return textwrap.indent(text, indent)


class DependencyListFormatter(NestedObjectFormatter):
    def format_console(self, value: Any, field: FieldSpec, indent="") -> str:
        assert isinstance(value, list)
        if len(value) == 0:
            text = "(no dependency tasks)"
        else:
            text = ""
            for item in value:
                text += f"+ {item['name']} ({item['id']})\n"
                text += "\n".join(
                    f"  - {f.humanized_name}: "
                    f"{_fit_multiline_in_cell(f.formatter.format_console(item[f.field_name], f), '    ')}"  # noqa
                    for f in field.subfields.values()
                    if f.field_name not in ("id", "name")
                )
        return textwrap.indent(text, indent)
