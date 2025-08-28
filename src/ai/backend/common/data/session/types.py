from enum import StrEnum


class CustomizedImageVisibilityScope(StrEnum):
    USER = "user"
    PROJECT = "project"


class ResourceSlotState(StrEnum):
    OCCUPIED = "occupied"
    AVAILABLE = "available"
