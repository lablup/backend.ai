from typing import override

from ai.backend.common.events.types import AbstractBroadcastEvent

from . import ModelServiceStatusEventArgs


class ModelServiceStatusBroadcastEvent(ModelServiceStatusEventArgs, AbstractBroadcastEvent):
    @classmethod
    @override
    def event_name(cls) -> str:
        return "model_service_status_updated"
