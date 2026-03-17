"""Base adapter class for transport-agnostic service invocation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ai.backend.manager.api.rest.adapter import BaseFilterAdapter

if TYPE_CHECKING:
    from ai.backend.manager.services.processors import Processors


class BaseAdapter(BaseFilterAdapter):
    """Transport-agnostic adapter base.

    Accepts Pydantic DTOs, invokes Processor actions, returns Pydantic DTOs.
    Subclass per domain and implement concrete create/read/update/delete methods.

    Inherits ``BaseFilterAdapter`` for reusable StringFilter/UUIDFilter
    conversion utilities (``convert_string_filter``, ``convert_uuid_filter``).

    Adapters do NOT contain business logic — they translate between
    the DTO layer and the Processor/Action layer.
    """

    def __init__(self, processors: Processors) -> None:
        self._processors = processors
