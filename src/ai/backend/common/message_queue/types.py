from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from typing import NewType, Self

from opentelemetry import trace
from opentelemetry.propagate import extract, inject
from opentelemetry.trace import SpanKind
from pydantic import BaseModel, ConfigDict

from ai.backend.common.contexts.request_id import current_request_id, with_request_context
from ai.backend.common.contexts.user import current_user, triggered_user, with_user_context
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
    # W3C trace context of the sender's span. Absent in messages from older senders.
    traceparent: str | None = None

    @classmethod
    def from_current_context(cls) -> Self:
        carrier: dict[str, str] = {}
        inject(carrier)
        return cls(
            request_id=current_request_id(),
            user=current_user(),
            triggered_user=triggered_user(),
            traceparent=carrier.get("traceparent"),
        )

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

    @contextmanager
    def continue_trace(self, span_name: str, kind: SpanKind) -> Iterator[None]:
        """Open a span under the sender's span. Opens none when the sender had no span."""
        if self.traceparent is None:
            yield
            return
        with trace.get_tracer(__name__).start_as_current_span(
            span_name,
            context=extract({"traceparent": self.traceparent}),
            kind=kind,
        ):
            yield
