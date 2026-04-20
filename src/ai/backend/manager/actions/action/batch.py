from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, TypeVar, override

from .base import BaseAction, BaseActionResult


@dataclass
class BaseBatchAction[T](BaseAction):
    """Base class for actions operating on a batch of entities.

    ``entity_ids`` is stored as ``list[str]`` so ``BatchActionValidator``
    implementations can match against validator verdicts directly. The
    original ``T``-typed view is exposed via ``typed_entity_ids()``.

    Batch actions intentionally carry **only** ``entity_ids``. User context
    (user id, role) flows through ``current_user()``, not the action, so
    ``BatchActionProcessor`` can reconstruct a filtered action by calling
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


class BaseBatchActionResult(BaseActionResult):
    @override
    def entity_id(self) -> str | None:
        return None

    @abstractmethod
    def entity_ids(self) -> list[str]:
        raise NotImplementedError


TBatchAction = TypeVar("TBatchAction", bound=BaseBatchAction[Any])
TBatchActionResult = TypeVar("TBatchActionResult", bound=BaseBatchActionResult)
