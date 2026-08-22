"""The wired domain operation catalog, read without a running manager.

The catalog is a record made while processors are assembled, and assembly stores
handlers rather than calling them, so reading it needs no dependency stage started.
It holds what the registry records: processors wired through a ``ProcessorGroup``.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, cast

from ai.backend.common.events.fetcher import EventFetcher
from ai.backend.common.events.hub.hub import EventHub
from ai.backend.manager.actions.monitors import ActionMonitors
from ai.backend.manager.actions.registry.types import WiredProcessor
from ai.backend.manager.actions.v2 import validators as v2_validators
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.services.factory import create_processors
from ai.backend.manager.services.processors import ProcessorArgs, ServiceArgs


class _Unwired:
    """Stands in for a runtime object the assembled processors would call."""

    def __getattr__(self, name: str) -> Any:
        return _Unwired()

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return _Unwired()


async def load_wiring_catalog() -> Sequence[WiredProcessor]:
    """Every wiring the processor assembly makes, in wiring order.

    Async because building some services allocates a task group, which needs a loop.
    """
    unwired = _Unwired()
    bundle = create_processors(
        ProcessorArgs(
            service_args=cast(ServiceArgs, unwired),
            event_hub=cast(EventHub, unwired),
            event_fetcher=cast(EventFetcher, unwired),
            validators=v2_validators.ActionValidators(),
        ),
        ActionMonitors(),
        cast(ActionValidators, unwired),
    )
    return bundle.registry.wired_processors()
