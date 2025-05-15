from __future__ import annotations

import logging
import re
from collections.abc import (
    Mapping,
    Sequence,
)
from dataclasses import dataclass
from typing import (
    Any,
    FrozenSet,
    Literal,
    NotRequired,
    Optional,
    Tuple,
    TypedDict,
    Union,
)

from ai.backend.common.enum_extension import StringSetFlag
from ai.backend.logging import BraceStyleAdapter

from .exception import UnsupportedBaseDistroError

log = BraceStyleAdapter(logging.getLogger(__spec__.name))

# msg types visible to the API client.
# (excluding control signals such as 'finished' and 'waiting-input'
# since they are passed as separate status field.)
ConsoleItemType = Literal[
    "stdout",
    "stderr",
    "media",
    "html",
    "log",
    "completion",
]
outgoing_msg_types: FrozenSet[ConsoleItemType] = frozenset([
    "stdout",
    "stderr",
    "media",
    "html",
    "log",
    "completion",
])
ResultType = Union[
    ConsoleItemType,
    Literal[
        "continued",
        "clean-finished",
        "build-finished",
        "finished",
        "exec-timeout",
        "waiting-input",
    ],
]


class ClientFeatures(StringSetFlag):
    INPUT = "input"
    CONTINUATION = "continuation"


# TODO: use Python 3.7 contextvars for per-client feature selection
default_client_features = frozenset({
    ClientFeatures.INPUT.value,
    ClientFeatures.CONTINUATION.value,
})
default_api_version = 4


class RunEvent(Exception):
    data: Any

    def __init__(self, data=None):
        super().__init__()
        self.data = data


class InputRequestPending(RunEvent):
    pass


class CleanFinished(RunEvent):
    pass


class BuildFinished(RunEvent):
    pass


class RunFinished(RunEvent):
    pass


class ExecTimeout(RunEvent):
    pass


@dataclass
class ResultRecord:
    msg_type: ResultType
    data: Optional[str] = None


class NextResult(TypedDict):
    runId: Optional[str]
    status: ResultType
    exitCode: Optional[int]
    options: Optional[Mapping[str, Any]]
    # v1
    stdout: NotRequired[Optional[str]]
    stderr: NotRequired[Optional[str]]
    media: NotRequired[Sequence[Any]]
    html: NotRequired[Sequence[Any]]
    # v2
    console: NotRequired[Sequence[Any]]


def match_distro_data(data: Mapping[str, Any], distro: str) -> Tuple[str, Any]:
    """
    Find the latest or exactly matching entry from krunner_volumes mapping using the given distro
    string expression.

    It assumes that the keys of krunner_volumes mapping is a string concatenated with a distro
    prefix (e.g., "centos", "ubuntu") and a distro version composed of multiple integer components
    joined by single dots (e.g., "1.2.3", "18.04").
    """
    rx_ver_suffix = re.compile(r"(\d+(\.\d+)*)$")

    def _extract_version(key: str) -> Tuple[int, ...]:
        m = rx_ver_suffix.search(key)
        if m is not None:
            return tuple(map(int, m.group(1).split(".")))
        return (0,)

    m = rx_ver_suffix.search(distro)
    if m is None:
        # Assume latest
        distro_prefix = distro
        distro_ver = None
    else:
        distro_prefix = distro[: -len(m.group(1))]
        distro_ver = tuple(map(int, m.group(1).split(".")))

    # Check if there are static-build krunners first.
    if distro_prefix == "alpine":
        libc_flavor = "musl"
    else:
        libc_flavor = "gnu"
    distro_key = f"static-{libc_flavor}"
    if volume := data.get(distro_key):
        return distro_key, volume

    # Search through the per-distro versions
    match_list = [
        (distro_key, value, _extract_version(distro_key))
        for distro_key, value in data.items()
        if distro_key.startswith(distro_prefix)
    ]

    match_list = sorted(match_list, key=lambda x: x[2], reverse=True)
    if match_list:
        if distro_ver is None:
            return match_list[0][:-1]  # return latest
        for distro_key, value, matched_distro_ver in match_list:
            if distro_ver >= matched_distro_ver:
                return (distro_key, value)
        return match_list[-1][:-1]  # fallback to the latest of its kind
    raise UnsupportedBaseDistroError(distro)
