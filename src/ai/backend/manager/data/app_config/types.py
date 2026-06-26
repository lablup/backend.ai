from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai.backend.manager.data.app_config_fragment.types import AppConfigFragmentData


@dataclass(frozen=True)
class AppConfigData:
    """Merged per-user view of one ``config_name`` (BEP-1052).

    The ordered contributing ``fragments`` (rank low -> high) plus their deep-merged
    ``config``. ``config`` is ``None`` when the merge of every fragment is empty.
    """

    config_name: str
    fragments: list[AppConfigFragmentData]
    config: dict[str, Any] | None
