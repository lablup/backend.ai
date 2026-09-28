from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from typing import NewType, Self

from pydantic import BaseModel, ConfigDict

from ai.backend.common.contexts.request_id import with_request_context
from ai.backend.common.contexts.user import with_user_context
from ai.backend.common.data.user.types import UserData

# What a message is routed by: consumers and subscribers are registered under it.
# It carries the name of the event the message was built from.
MessageName = NewType("MessageName", str)


class MessageMetadata(BaseModel):
    """
    The ambient context captured by the producer so the consumer can restore it."""

    model_config = ConfigDict(frozen=True)

    request_id: str | None = None
    user: UserData | None = None
    triggered_user: UserData | None = None

    def serialize(self) -> bytes:
        """
        Serialize the metadata to bytes.
        """
        return self.model_dump_json().encode("utf-8")

    @classmethod
    def deserialize(cls, data: str | bytes) -> Self:
        """
        Deserialize the metadata from bytes.
        """
        return cls.model_validate_json(data)

    @contextmanager
    def apply_context(self) -> Iterator[None]:
        """
        Context manager to apply all context variables stored in metadata.
        """
        with ExitStack() as stack:
            if self.request_id:
                stack.enter_context(with_request_context(self.request_id))
            stack.enter_context(with_user_context(self.user, self.triggered_user))
            yield
