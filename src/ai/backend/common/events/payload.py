from pydantic import BaseModel, ConfigDict

__all__ = (
    "AnycastEventPayload",
    "BroadcastEventPayload",
)


class AnycastEventPayload(BaseModel):
    """
    Base of every anycast event's payload — the body an event carries, as named and
    typed fields instead of a positional tuple.

    A field may be added or given a default without breaking a reader running a
    different version, which a tuple position cannot offer.

    This is the event's own body, distinct from `AnycastMessagePayload`, which is what
    the message queue wraps it in to deliver it.
    """

    model_config = ConfigDict(frozen=True)


class BroadcastEventPayload(BaseModel):
    """
    Base of every broadcast event's payload — the body an event carries, as named and
    typed fields instead of a positional tuple.

    Kept separate from `AnycastEventPayload` so an event cannot declare a payload of
    the delivery pattern it does not use.
    """

    model_config = ConfigDict(frozen=True)
