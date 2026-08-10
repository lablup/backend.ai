from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from typing import Self

from ai.backend.common.contexts.request_id import with_request_id
from ai.backend.common.contexts.user import with_triggered_user, with_user
from ai.backend.common.data.user.types import UserData
from ai.backend.common.json import dump_json, load_json
from ai.backend.logging.utils import with_log_context_fields


@dataclass
class MessageMetadata:
    request_id: str | None = None
    user: UserData | None = None
    triggered_user: UserData | None = None

    def serialize(self) -> bytes:
        """
        Serialize the metadata to bytes.
        """
        return dump_json(self)

    @classmethod
    def deserialize(cls, data: str | bytes) -> Self:
        """
        Deserialize the metadata from bytes.
        """
        result = load_json(data)
        if "user_id" in result:
            del result["user_id"]
        for key in ("user", "triggered_user"):
            if key in result:
                user_data = result[key]
                if isinstance(user_data, dict):
                    result[key] = UserData.from_dict(user_data)
                else:
                    result[key] = None
        return cls(**result)

    @contextmanager
    def apply_context(self) -> Iterator[None]:
        """
        Context manager to apply all context variables stored in metadata.
        """
        with ExitStack() as stack:
            log_fields: dict[str, str] = {}
            if self.request_id:
                stack.enter_context(with_request_id(self.request_id))
                log_fields["request_id"] = self.request_id
            if self.user:
                stack.enter_context(with_user(self.user))
                log_fields["user_id"] = str(self.user.user_id)
            if self.triggered_user:
                stack.enter_context(with_triggered_user(self.triggered_user))
                log_fields["triggered_user_id"] = str(self.triggered_user.user_id)
            if log_fields:
                stack.enter_context(with_log_context_fields(log_fields))
            yield
