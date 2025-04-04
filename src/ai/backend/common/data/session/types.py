import enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class CustomizedImageVisibilityScope(str, enum.Enum):
    USER = "user"
    PROJECT = "project"
