from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from multidict import CIMultiDictProxy, MultiMapping


@dataclass
class HTTPRequestData:
    """The parts of an inbound request an authentication plugin may read.

    Headers and query parameters keep their multi-dict form: copying them into a
    plain dict drops repeated keys and, for headers, case-insensitive lookup.
    """

    headers: CIMultiDictProxy[str]
    body: Mapping[str, Any] | None
    cookies: Mapping[str, str]
    query_params: MultiMapping[str]
