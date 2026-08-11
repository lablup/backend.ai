from typing import Final, Self

from pydantic import BaseModel, ConfigDict

from .payload import AnycastPayload

_DEFAULT_MAX_RETRIES: Final[int] = 3

type MessageId = bytes


class MQMessage(BaseModel):
    """An anycast payload together with the stream entry id needed to ack it."""

    model_config = ConfigDict(frozen=True)

    msg_id: MessageId
    payload: AnycastPayload

    def retry(self) -> Self | None:
        """
        Return a copy of the message carrying an incremented retry count.
        Returns None once the message has been retried more than the maximum number
        of times, meaning it should be discarded.
        """
        if self.payload.retry_count > _DEFAULT_MAX_RETRIES:
            return None
        return self.model_copy(update={"payload": self.payload.increment_retry()})
