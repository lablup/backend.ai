"""Session GraphQL payload types for mutations."""

from __future__ import annotations

from uuid import UUID

import strawberry

from .types import SessionV2GQL

# Modify Session


@strawberry.type(
    name="ModifySessionV2Payload",
    description="Added in 26.3.0. Payload for session modification mutation.",
)
class ModifySessionV2PayloadGQL:
    """Payload for session modification."""

    session: SessionV2GQL = strawberry.field(description="The modified session.")


# Check and Transit Status


@strawberry.type(
    name="CheckAndTransitSessionV2StatusPayload",
    description="Added in 26.3.0. Payload for session status check and transition mutation.",
)
class CheckAndTransitSessionV2StatusPayloadGQL:
    """Payload for session status check and transition."""

    sessions: list[SessionV2GQL] = strawberry.field(
        description="List of sessions whose status was checked and potentially transitioned."
    )


# Destroy Session


@strawberry.type(
    name="DestroySessionV2Payload",
    description="Added in 26.3.0. Payload for session destruction mutation.",
)
class DestroySessionV2PayloadGQL:
    """Payload for session destruction."""

    success: bool = strawberry.field(description="Whether the session was successfully destroyed.")


# Restart Session


@strawberry.type(
    name="RestartSessionV2Payload",
    description="Added in 26.3.0. Payload for session restart mutation.",
)
class RestartSessionV2PayloadGQL:
    """Payload for session restart."""

    success: bool = strawberry.field(description="Whether the session restart was initiated.")


# Rename Session


@strawberry.type(
    name="RenameSessionV2Payload",
    description="Added in 26.3.0. Payload for session rename mutation.",
)
class RenameSessionV2PayloadGQL:
    """Payload for session rename."""

    success: bool = strawberry.field(description="Whether the session was successfully renamed.")


# Interrupt Session


@strawberry.type(
    name="InterruptSessionV2Payload",
    description="Added in 26.3.0. Payload for session interrupt mutation.",
)
class InterruptSessionV2PayloadGQL:
    """Payload for session interrupt."""

    success: bool = strawberry.field(
        description="Whether the interrupt signal was successfully sent."
    )


# Execute in Session


@strawberry.type(
    name="ExecuteInSessionV2Payload",
    description="Added in 26.3.0. Payload for code execution in session mutation.",
)
class ExecuteInSessionV2PayloadGQL:
    """Payload for code execution in session."""

    success: bool = strawberry.field(description="Whether the code execution was initiated.")


# Commit Session


@strawberry.type(
    name="CommitSessionV2Payload",
    description="Added in 26.3.0. Payload for session commit mutation.",
)
class CommitSessionV2PayloadGQL:
    """Payload for session commit."""

    success: bool = strawberry.field(description="Whether the session commit was initiated.")


# Convert Session to Image


@strawberry.type(
    name="ConvertSessionV2ToImagePayload",
    description="Added in 26.3.0. Payload for session-to-image conversion mutation.",
)
class ConvertSessionV2ToImagePayloadGQL:
    """Payload for session-to-image conversion."""

    task_id: UUID = strawberry.field(
        description="UUID of the background task handling the conversion."
    )


# Start Session Service


@strawberry.type(
    name="StartSessionV2ServicePayload",
    description="Added in 26.3.0. Payload for starting an app service within a session.",
)
class StartSessionV2ServicePayloadGQL:
    """Payload for starting a session service."""

    success: bool = strawberry.field(description="Whether the service was successfully started.")


# Shutdown Session Service


@strawberry.type(
    name="ShutdownSessionV2ServicePayload",
    description="Added in 26.3.0. Payload for shutting down an app service within a session.",
)
class ShutdownSessionV2ServicePayloadGQL:
    """Payload for shutting down a session service."""

    success: bool = strawberry.field(description="Whether the service was successfully shut down.")


# Complete Session Code


@strawberry.type(
    name="CompleteSessionV2CodePayload",
    description="Added in 26.3.0. Payload for code auto-completion in session mutation.",
)
class CompleteSessionV2CodePayloadGQL:
    """Payload for code auto-completion."""

    success: bool = strawberry.field(description="Whether code completion was successful.")


# Create Session (shared payload for all create variants)


@strawberry.type(
    name="CreateSessionV2Payload",
    description=(
        "Added in 26.3.0. Payload for session creation mutations. "
        "Shared by create-from-params, create-from-template, and create-cluster."
    ),
)
class CreateSessionV2PayloadGQL:
    """Payload for session creation."""

    session_id: UUID = strawberry.field(description="UUID of the newly created session.")
