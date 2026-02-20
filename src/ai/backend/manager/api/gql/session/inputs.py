"""Session GraphQL input types for mutations."""

from __future__ import annotations

from uuid import UUID

import strawberry

from ai.backend.manager.api.gql.common.types import ClusterModeGQL, SessionV2TypeGQL

# Modify Session


@strawberry.input(
    name="ModifySessionV2Input",
    description=(
        "Added in 26.3.0. Input for modifying session properties (admin only). "
        "Only provided fields will be updated."
    ),
)
class ModifySessionV2InputGQL:
    """Input for modifying a session."""

    session_id: UUID = strawberry.field(description="UUID of the session to modify.")
    name: str | None = strawberry.field(
        default=None,
        description="New name for the session.",
    )
    priority: int | None = strawberry.field(
        default=None,
        description="New scheduling priority for the session.",
    )


# Check and Transit Status


@strawberry.input(
    name="CheckAndTransitSessionV2StatusInput",
    description=(
        "Added in 26.3.0. Input for checking and transitioning session status. "
        "Checks the actual status of sessions and updates them accordingly."
    ),
)
class CheckAndTransitSessionV2StatusInputGQL:
    """Input for checking and transitioning session status."""

    session_ids: list[UUID] = strawberry.field(
        description="List of session UUIDs to check and transit."
    )


# Destroy Session


@strawberry.input(
    name="DestroySessionV2Input",
    description=(
        "Added in 26.3.0. Input for terminating/deleting a session. "
        "Supports forced termination and recursive deletion."
    ),
)
class DestroySessionV2InputGQL:
    """Input for destroying a session."""

    session_name: str = strawberry.field(description="Name or ID of the session to destroy.")
    forced: bool = strawberry.field(
        default=False,
        description="If true, forcibly terminate the session without graceful shutdown.",
    )
    recursive: bool = strawberry.field(
        default=False,
        description="If true, recursively destroy dependent sessions.",
    )
    owner_access_key: str | None = strawberry.field(
        default=None,
        description="Access key of the session owner. Required for admin operations on behalf of users.",
    )


# Restart Session


@strawberry.input(
    name="RestartSessionV2Input",
    description="Added in 26.3.0. Input for restarting a session.",
)
class RestartSessionV2InputGQL:
    """Input for restarting a session."""

    session_name: str = strawberry.field(description="Name or ID of the session to restart.")
    owner_access_key: str | None = strawberry.field(
        default=None,
        description="Access key of the session owner. Required for admin operations on behalf of users.",
    )


# Rename Session


@strawberry.input(
    name="RenameSessionV2Input",
    description="Added in 26.3.0. Input for renaming a session.",
)
class RenameSessionV2InputGQL:
    """Input for renaming a session."""

    session_name: str = strawberry.field(description="Current name or ID of the session.")
    new_name: str = strawberry.field(description="New name for the session.")
    owner_access_key: str | None = strawberry.field(
        default=None,
        description="Access key of the session owner. Required for admin operations on behalf of users.",
    )


# Interrupt Session


@strawberry.input(
    name="InterruptSessionV2Input",
    description="Added in 26.3.0. Input for interrupting a running session.",
)
class InterruptSessionV2InputGQL:
    """Input for interrupting a session."""

    session_name: str = strawberry.field(description="Name or ID of the session to interrupt.")
    owner_access_key: str | None = strawberry.field(
        default=None,
        description="Access key of the session owner. Required for admin operations on behalf of users.",
    )


# Execute in Session


@strawberry.input(
    name="ExecuteInSessionV2Input",
    description=(
        "Added in 26.3.0. Input for executing code in a session. "
        "Supports different execution modes (query, batch, input, continue)."
    ),
)
class ExecuteInSessionV2InputGQL:
    """Input for executing code in a session."""

    session_name: str = strawberry.field(description="Name or ID of the session to execute in.")
    code: str | None = strawberry.field(
        default=None,
        description="Code to execute.",
    )
    mode: str = strawberry.field(
        default="query",
        description="Execution mode: 'query', 'batch', 'input', or 'continue'.",
    )
    run_id: str | None = strawberry.field(
        default=None,
        description="Run ID for tracking multi-step executions.",
    )
    options: str | None = strawberry.field(
        default=None,
        description="JSON string of execution options.",
    )
    owner_access_key: str | None = strawberry.field(
        default=None,
        description="Access key of the session owner. Required for admin operations on behalf of users.",
    )


# Commit Session


@strawberry.input(
    name="CommitSessionV2Input",
    description="Added in 26.3.0. Input for committing the current session state.",
)
class CommitSessionV2InputGQL:
    """Input for committing a session."""

    session_name: str = strawberry.field(description="Name or ID of the session to commit.")
    filename: str | None = strawberry.field(
        default=None,
        description="Optional filename for the committed state.",
    )
    owner_access_key: str | None = strawberry.field(
        default=None,
        description="Access key of the session owner. Required for admin operations on behalf of users.",
    )


# Convert Session to Image


@strawberry.input(
    name="ConvertSessionV2ToImageInput",
    description="Added in 26.3.0. Input for converting a session to a container image.",
)
class ConvertSessionV2ToImageInputGQL:
    """Input for converting a session to a container image."""

    session_name: str = strawberry.field(description="Name or ID of the session to convert.")
    image_name: str = strawberry.field(description="Name for the resulting container image.")
    owner_access_key: str | None = strawberry.field(
        default=None,
        description="Access key of the session owner. Required for admin operations on behalf of users.",
    )


# Start Session Service


@strawberry.input(
    name="StartSessionV2ServiceInput",
    description=(
        "Added in 26.3.0. Input for starting an app service within a session. "
        "Services include Jupyter, TensorBoard, SSH, etc."
    ),
)
class StartSessionV2ServiceInputGQL:
    """Input for starting a service in a session."""

    session_name: str = strawberry.field(description="Name or ID of the session.")
    service: str = strawberry.field(description="Name of the service to start (e.g., 'jupyter').")
    port: int | None = strawberry.field(
        default=None,
        description="Optional port number for the service.",
    )
    arguments: str | None = strawberry.field(
        default=None,
        description="JSON string of additional arguments for the service.",
    )
    envs: str | None = strawberry.field(
        default=None,
        description="JSON string of environment variables for the service.",
    )
    owner_access_key: str | None = strawberry.field(
        default=None,
        description="Access key of the session owner. Required for admin operations on behalf of users.",
    )


# Shutdown Session Service


@strawberry.input(
    name="ShutdownSessionV2ServiceInput",
    description="Added in 26.3.0. Input for shutting down an app service within a session.",
)
class ShutdownSessionV2ServiceInputGQL:
    """Input for shutting down a service in a session."""

    session_name: str = strawberry.field(description="Name or ID of the session.")
    service_name: str = strawberry.field(description="Name of the service to shut down.")
    owner_access_key: str | None = strawberry.field(
        default=None,
        description="Access key of the session owner. Required for admin operations on behalf of users.",
    )


# Complete Session Code


@strawberry.input(
    name="CompleteSessionV2CodeInput",
    description="Added in 26.3.0. Input for code auto-completion in a session.",
)
class CompleteSessionV2CodeInputGQL:
    """Input for code auto-completion in a session."""

    session_name: str = strawberry.field(description="Name or ID of the session.")
    code: str = strawberry.field(description="Code text for auto-completion.")
    options: str | None = strawberry.field(
        default=None,
        description="JSON string of completion options.",
    )
    owner_access_key: str | None = strawberry.field(
        default=None,
        description="Access key of the session owner. Required for admin operations on behalf of users.",
    )


# Create Session from Params


@strawberry.input(
    name="CreateSessionV2FromParamsInput",
    description=(
        "Added in 26.3.0. Input for creating a session with explicit parameters. "
        "Specifies image, resources, and configuration directly."
    ),
)
class CreateSessionV2FromParamsInputGQL:
    """Input for creating a session from explicit parameters."""

    session_name: str = strawberry.field(description="Name for the new session.")
    image: str = strawberry.field(description="Container image reference for the session.")
    session_type: SessionV2TypeGQL = strawberry.field(
        default=SessionV2TypeGQL.INTERACTIVE,
        description="Type of session to create.",
    )
    cluster_size: int = strawberry.field(
        default=1,
        description="Number of nodes in the cluster.",
    )
    cluster_mode: ClusterModeGQL = strawberry.field(
        default=ClusterModeGQL.SINGLE_NODE,
        description="Cluster mode for the session.",
    )
    tag: str | None = strawberry.field(
        default=None,
        description="Optional user-provided tag for the session.",
    )
    priority: int = strawberry.field(
        default=0,
        description="Scheduling priority for the session.",
    )
    owner_access_key: str | None = strawberry.field(
        default=None,
        description="Access key of the session owner. Required for admin operations on behalf of users.",
    )
    enqueue_only: bool = strawberry.field(
        default=False,
        description="If true, only enqueue the session without waiting for it to start.",
    )
    max_wait_seconds: int = strawberry.field(
        default=0,
        description="Maximum seconds to wait for the session to be ready.",
    )
    starts_at: str | None = strawberry.field(
        default=None,
        description="Scheduled start time for the session (ISO 8601 format).",
    )
    startup_command: str | None = strawberry.field(
        default=None,
        description="Command to execute when the session starts.",
    )
    bootstrap_script: str | None = strawberry.field(
        default=None,
        description="Bootstrap script to run before the main process.",
    )
    callback_url: str | None = strawberry.field(
        default=None,
        description="URL to call back when the session completes.",
    )
    config: str | None = strawberry.field(
        default=None,
        description="JSON string of additional session configuration (resources, mounts, etc.).",
    )


# Create Session from Template


@strawberry.input(
    name="CreateSessionV2FromTemplateInput",
    description=(
        "Added in 26.3.0. Input for creating a session from a predefined template. "
        "Template values can be overridden with provided fields."
    ),
)
class CreateSessionV2FromTemplateInputGQL:
    """Input for creating a session from a template."""

    template_id: UUID = strawberry.field(description="UUID of the session template to use.")
    session_name: str | None = strawberry.field(
        default=None,
        description="Override name for the session. Uses template default if not provided.",
    )
    image: str | None = strawberry.field(
        default=None,
        description="Override container image. Uses template default if not provided.",
    )
    session_type: SessionV2TypeGQL | None = strawberry.field(
        default=None,
        description="Override session type. Uses template default if not provided.",
    )
    cluster_size: int | None = strawberry.field(
        default=None,
        description="Override cluster size. Uses template default if not provided.",
    )
    cluster_mode: ClusterModeGQL | None = strawberry.field(
        default=None,
        description="Override cluster mode. Uses template default if not provided.",
    )
    tag: str | None = strawberry.field(
        default=None,
        description="Optional user-provided tag for the session.",
    )
    priority: int | None = strawberry.field(
        default=None,
        description="Override scheduling priority. Uses template default if not provided.",
    )
    owner_access_key: str | None = strawberry.field(
        default=None,
        description="Access key of the session owner. Required for admin operations on behalf of users.",
    )
    enqueue_only: bool = strawberry.field(
        default=False,
        description="If true, only enqueue the session without waiting for it to start.",
    )
    max_wait_seconds: int = strawberry.field(
        default=0,
        description="Maximum seconds to wait for the session to be ready.",
    )
    starts_at: str | None = strawberry.field(
        default=None,
        description="Scheduled start time for the session (ISO 8601 format).",
    )
    startup_command: str | None = strawberry.field(
        default=None,
        description="Override startup command. Uses template default if not provided.",
    )
    bootstrap_script: str | None = strawberry.field(
        default=None,
        description="Override bootstrap script. Uses template default if not provided.",
    )
    callback_url: str | None = strawberry.field(
        default=None,
        description="URL to call back when the session completes.",
    )
    config: str | None = strawberry.field(
        default=None,
        description="JSON string of additional session configuration overrides.",
    )


# Create Session Cluster


@strawberry.input(
    name="CreateSessionV2ClusterInput",
    description=(
        "Added in 26.3.0. Input for creating a cluster session. "
        "Creates a multi-node session based on a template."
    ),
)
class CreateSessionV2ClusterInputGQL:
    """Input for creating a cluster session."""

    session_name: str = strawberry.field(description="Name for the cluster session.")
    template_id: UUID = strawberry.field(description="UUID of the session template to use.")
    session_type: SessionV2TypeGQL = strawberry.field(
        default=SessionV2TypeGQL.INTERACTIVE,
        description="Type of session to create.",
    )
    tag: str | None = strawberry.field(
        default=None,
        description="Optional user-provided tag for the session.",
    )
    owner_access_key: str | None = strawberry.field(
        default=None,
        description="Access key of the session owner. Required for admin operations on behalf of users.",
    )
    enqueue_only: bool = strawberry.field(
        default=False,
        description="If true, only enqueue the session without waiting for it to start.",
    )
    max_wait_seconds: int = strawberry.field(
        default=0,
        description="Maximum seconds to wait for the session to be ready.",
    )
    scaling_group_name: str | None = strawberry.field(
        default=None,
        description="Name of the scaling group (resource group) to use.",
    )
