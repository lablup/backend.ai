from pydantic import BaseModel, ConfigDict

from ai.backend.common.message_queue.types import MessageName

__all__ = ("EventMessage",)


class EventMessage(BaseModel):
    """
    What an event hands to the message queue: what it is, and its body already
    serialized.

    This is everything an event can know about the message it becomes. The rest of
    what a delivered message carries — the producing node, the ambient context, the
    transport's redelivery state — is filled in by the producer and the transport,
    so it lives on `AnycastMessagePayload` / `BroadcastMessagePayload` instead.

    A single type serves both delivery patterns: the body is the same either way,
    and which pattern an event uses is already declared by the base it derives from.
    """

    model_config = ConfigDict(frozen=True)

    name: MessageName
    payload: str
