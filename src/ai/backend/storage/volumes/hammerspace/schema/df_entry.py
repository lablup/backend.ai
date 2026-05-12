from ai.backend.common.types import BackendAISchema


class DFEntry(BackendAISchema):
    total: int
    used: int
    available: int
    percent: int
