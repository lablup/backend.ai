from ai.backend.common.types import BackendAISchema


class Capacity(BackendAISchema):
    total: int
    used: int
    free: int
