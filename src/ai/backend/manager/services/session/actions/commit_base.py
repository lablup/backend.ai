from dataclasses import dataclass

from ai.backend.manager.services.session.base import SessionAction


@dataclass
class SessionCommitAction(SessionAction):
    """Base for an operation on committing a session to an image.

    Answered for by the session: what is touched lives inside it and holds no
    membership of its own.
    """
