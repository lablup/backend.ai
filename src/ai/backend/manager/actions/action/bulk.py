from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, TypeVar, override

from .base import BaseAction, BaseActionResult


@dataclass
class BaseBulkAction[T](BaseAction):
    """Base class for actions operating on a bulk of entities.

    ``entity_ids`` is stored as ``list[str]`` so ``BulkActionValidator``
    implementations can match against validator verdicts directly. The
    original ``T``-typed view is exposed via ``typed_entity_ids()``.

    Bulk actions intentionally carry **only** ``entity_ids``. User context
    (user id, role) flows through ``current_user()``, not the action, so
    ``BulkActionProcessor`` can reconstruct a filtered action by calling
    ``type(action)(entity_ids=...)`` directly — no ``__init__`` override or
    factory hook is required. Subclasses that try to add required fields
    break that constructor call and will fail fast at runtime, which is
    intentional.
    """

    entity_ids: list[str]

    @abstractmethod
    def typed_entity_ids(self) -> list[T]:
        """Return ``entity_ids`` converted back to the native ID type ``T``."""
        raise NotImplementedError


class BaseBulkActionResult(BaseActionResult):
    @override
    def entity_id(self) -> str | None:
        return None

    @abstractmethod
    def entity_ids(self) -> list[str]:
        raise NotImplementedError


TBulkAction = TypeVar("TBulkAction", bound=BaseBulkAction[Any])
TBulkActionResult = TypeVar("TBulkActionResult", bound=BaseBulkActionResult)
